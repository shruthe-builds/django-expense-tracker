import re
from datetime import date
from django.contrib.auth.models import User
from django.db import models

# Smart category prediction: simple keyword dictionary (easy to extend / swap for NLP later)
KEYWORDS = {
    'Travel': ['uber', 'ola', 'taxi', 'bus', 'train', 'metro', 'flight', 'petrol', 'fuel', 'cab', 'auto'],
    'Food': ['pizza', 'burger', 'lunch', 'dinner', 'breakfast', 'swiggy', 'zomato', 'coffee', 'tea', 'restaurant', 'snack', 'biryani'],
    'Shopping': ['amazon', 'flipkart', 'shirt', 'shoes', 'clothes', 'mall', 'myntra'],
    'Bills': ['electricity', 'water', 'wifi', 'internet', 'recharge', 'rent', 'bill', 'gas'],
    'Entertainment': ['movie', 'netflix', 'spotify', 'game', 'concert', 'cinema'],
    'Education': ['book', 'course', 'tuition', 'fees', 'exam', 'stationery', 'notebook'],
    'Health': ['doctor', 'medicine', 'pharmacy', 'hospital', 'gym', 'clinic'],
}


def predict_category(description):
    """Return the first category with a keyword that appears as a whole word."""
    words = set(re.findall(r"[a-z]+", description.lower()))
    words |= {w[:-1] for w in words if w.endswith('s') and len(w) > 3}  # "pizzas" -> "pizza"
    for category, keys in KEYWORDS.items():
        if any(key in words for key in keys):
            return category
    return 'Other'


class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, blank=True)
    date = models.DateField(default=date.today)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-id']

    def save(self, *args, **kwargs):
        if not self.category:
            self.category = predict_category(self.description)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.description} - {self.amount}'
