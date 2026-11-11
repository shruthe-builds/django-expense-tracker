import csv
from datetime import date, timedelta
from collections import OrderedDict

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ExpenseForm, SignUpForm
from .models import Expense


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.save())
        return redirect('dashboard')
    return render(request, 'registration/signup.html', {'form': form})


def filtered_expenses(request):
    """Only the logged-in user's expenses, filtered by ?range=today|week|month|all"""
    rng = request.GET.get('range', 'all')
    qs = Expense.objects.filter(user=request.user)
    today = date.today()
    if rng == 'today':
        qs = qs.filter(date=today)
    elif rng == 'week':
        qs = qs.filter(date__gte=today - timedelta(days=today.weekday()), date__lte=today)
    elif rng == 'month':
        qs = qs.filter(date__year=today.year, date__month=today.month)
    return qs, rng


@login_required
def dashboard(request):
    expenses, rng = filtered_expenses(request)
    total = expenses.aggregate(t=Sum('amount'))['t'] or 0

    cat_totals = expenses.values('category').annotate(t=Sum('amount')).order_by('-t')
    by_date = OrderedDict()
    for e in reversed(list(expenses)):
        by_date[str(e.date)] = by_date.get(str(e.date), 0) + float(e.amount)

    chart = {
        'cat_labels': [c['category'] for c in cat_totals],
        'cat_values': [float(c['t']) for c in cat_totals],
        'date_labels': list(by_date.keys()),
        'date_values': list(by_date.values()),
    }
    return render(request, 'dashboard.html',
                  {'expenses': expenses, 'total': total, 'range': rng, 'chart': chart})


@login_required
def add_expense(request):
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        exp = form.save(commit=False)
        exp.user = request.user
        exp.save()
        return redirect('dashboard')
    return render(request, 'form.html', {'form': form, 'title': 'Add Expense'})


@login_required
def edit_expense(request, pk):
    exp = get_object_or_404(Expense, pk=pk, user=request.user)
    form = ExpenseForm(request.POST or None, instance=exp)   # pre-fills with old data
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'form.html', {'form': form, 'title': 'Edit Expense'})


@login_required
def delete_expense(request, pk):
    exp = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        exp.delete()
        return redirect('dashboard')
    return render(request, 'confirm_delete.html', {'expense': exp})


def _csv_safe(value):
    """Stop Excel/Sheets from running user text as a formula (CSV injection)."""
    text = str(value)
    return "'" + text if text[:1] in ('=', '+', '-', '@', '\t', '\r') else text


@login_required
def download_csv(request):
    expenses, _ = filtered_expenses(request)
    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="expenses.csv"'
    w = csv.writer(resp)
    w.writerow(['Date', 'Description', 'Category', 'Amount', 'Notes'])
    for e in expenses:
        w.writerow([e.date, _csv_safe(e.description), _csv_safe(e.category), e.amount, _csv_safe(e.notes)])
    return resp


@login_required
def download_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    expenses, _ = filtered_expenses(request)
    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="expenses.pdf"'
    data = [['Date', 'Description', 'Category', 'Amount']]
    total = 0
    for e in expenses:
        data.append([str(e.date), e.description[:35], e.category, f'{e.amount}'])
        total += e.amount
    data.append(['', '', 'TOTAL', f'{total}'])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    styles = getSampleStyleSheet()
    SimpleDocTemplate(resp, pagesize=A4).build(
        [Paragraph(f'Expense Report - {request.user.username}', styles['Title']), Spacer(1, 12), table])
    return resp
