from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Expense, predict_category


class PredictCategoryTests(TestCase):
    def test_known_keywords(self):
        self.assertEqual(predict_category('Uber to office'), 'Travel')
        self.assertEqual(predict_category('Pizza with friends'), 'Food')
        self.assertEqual(predict_category('Netflix subscription'), 'Entertainment')
        self.assertEqual(predict_category('Electricity bill'), 'Bills')

    def test_plural_words_match(self):
        self.assertEqual(predict_category('Two pizzas'), 'Food')

    def test_keywords_only_match_whole_words(self):
        # "bus" is inside "business" and "gas" inside "vegas": neither is a match
        self.assertEqual(predict_category('Business cards'), 'Other')
        self.assertEqual(predict_category('Vegas trip'), 'Other')

    def test_unknown_description_is_other(self):
        self.assertEqual(predict_category('Miscellaneous'), 'Other')


class ExpenseModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alice', password='pass12345')

    def test_category_is_predicted_when_blank(self):
        e = Expense.objects.create(user=self.user, description='Swiggy dinner', amount=Decimal('250'))
        self.assertEqual(e.category, 'Food')

    def test_explicit_category_is_kept(self):
        e = Expense.objects.create(user=self.user, description='Swiggy dinner',
                                   amount=Decimal('250'), category='Health')
        self.assertEqual(e.category, 'Health')


class ViewTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pass12345')
        self.bob = User.objects.create_user('bob', password='pass12345')
        self.expense = Expense.objects.create(
            user=self.alice, description='Uber ride', amount=Decimal('120.50'), date=date.today())
        self.client.login(username='alice', password='pass12345')

    def test_dashboard_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_dashboard_shows_only_own_expenses(self):
        Expense.objects.create(user=self.bob, description='Bob secret lunch', amount=Decimal('99'))
        resp = self.client.get(reverse('dashboard'))
        self.assertContains(resp, 'Uber ride')
        self.assertNotContains(resp, 'Bob secret lunch')

    def test_range_filter_today(self):
        Expense.objects.create(user=self.alice, description='Old purchase',
                               amount=Decimal('5'), date=date(2020, 1, 1))
        resp = self.client.get(reverse('dashboard') + '?range=today')
        self.assertContains(resp, 'Uber ride')
        self.assertNotContains(resp, 'Old purchase')

    def test_add_expense_sets_user_and_predicts_category(self):
        resp = self.client.post(reverse('add'), {
            'description': 'Metro ticket', 'amount': '30',
            'category': '', 'date': '2026-11-10', 'notes': ''})
        self.assertEqual(resp.status_code, 302)
        e = Expense.objects.get(description='Metro ticket')
        self.assertEqual(e.user, self.alice)
        self.assertEqual(e.category, 'Travel')

    def test_add_expense_rejects_non_positive_amount(self):
        resp = self.client.post(reverse('add'), {
            'description': 'Bad', 'amount': '-5',
            'category': '', 'date': '2026-11-10', 'notes': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Expense.objects.filter(description='Bad').exists())

    def test_cannot_edit_or_delete_another_users_expense(self):
        other = Expense.objects.create(user=self.bob, description='Bob thing', amount=Decimal('10'))
        self.assertEqual(self.client.get(reverse('edit', args=[other.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('delete', args=[other.pk])).status_code, 404)
        self.assertTrue(Expense.objects.filter(pk=other.pk).exists())

    def test_delete_own_expense(self):
        resp = self.client.post(reverse('delete', args=[self.expense.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Expense.objects.filter(pk=self.expense.pk).exists())

    def test_csv_export(self):
        resp = self.client.get(reverse('csv'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp['Content-Type'].startswith('text/csv'))
        self.assertIn('Uber ride', resp.content.decode())

    def test_csv_export_neutralises_formulas(self):
        Expense.objects.create(user=self.alice, description='=HYPERLINK("x")', amount=Decimal('1'))
        body = self.client.get(reverse('csv')).content.decode()
        self.assertIn("'=HYPERLINK", body)

    def test_pdf_export(self):
        resp = self.client.get(reverse('pdf'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF'))

    def test_signup_creates_user_and_logs_in(self):
        self.client.logout()
        resp = self.client.post(reverse('signup'), {
            'username': 'carol', 'password1': 'a-Strong-pass-123', 'password2': 'a-Strong-pass-123'})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='carol').exists())
