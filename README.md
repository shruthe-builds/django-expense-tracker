# Smart Expense Tracker

A Django web app for tracking personal expenses. Each user has a private account, adds expenses with a one-line description, and the app **suggests the category automatically**. A dashboard shows totals and charts, and the data can be exported as CSV or PDF.

## Features
- Sign up, log in and log out; every user sees only their own expenses
- Add, edit and delete expenses (description, amount, date, notes)
- **Automatic category prediction** from the description (e.g. "Swiggy dinner" becomes Food, "Uber to office" becomes Travel). It uses a keyword dictionary, not machine learning, and you can override the category by hand
- Dashboard with a total and filters for Today, This Week, This Month and All
- Category pie chart and spending-over-time bar chart (Chart.js)
- Export the current view as **CSV** or **PDF**
- Django admin for managing data

## Tech stack
Python 3.12+ · Django · SQLite · ReportLab (PDF export) · Bootstrap 5 and Chart.js (loaded from a CDN)

## Setup
```bash
git clone https://github.com/<your-username>/smart-expense-tracker.git
cd smart-expense-tracker
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Open http://127.0.0.1:8000/ and click **Sign Up** to create your account.

Optional: `python manage.py createsuperuser` creates an admin login for http://127.0.0.1:8000/admin/.

## Configuration
The defaults work for local development. For anything else, set these environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key | an insecure development key |
| `DJANGO_DEBUG` | `True` or `False` | `True` |
| `DJANGO_ALLOWED_HOSTS` | comma-separated host names | empty |

## Running the tests
```bash
python manage.py test
```
The tests cover category prediction, per-user data isolation, add/edit/delete, the date filters, CSV and PDF export, and sign-up.

## How category prediction works
`tracker/models.py` has a `KEYWORDS` dictionary that maps each category to a list of words. The first category with a keyword that appears as a whole word in the description wins; otherwise the category is `Other`. To teach it new words, add them to that dictionary.

## Project structure
```
config/              Django project settings and root URLs
tracker/             the app
  models.py          Expense model and category prediction
  views.py           dashboard, CRUD, CSV/PDF export, sign-up
  forms.py           expense and sign-up forms
  templates/         HTML pages (Bootstrap)
  tests.py           automated tests
manage.py
requirements.txt
```

## Limitations
- Built for local use and learning, not production: `DEBUG` is on by default, it uses SQLite, and there is no static-file or deployment setup.
- Bootstrap and Chart.js come from a CDN, so the styling and charts need an internet connection.
- The currency is fixed to rupees (₹).
- Category prediction is keyword-based, so unusual descriptions fall into `Other`.
- The PDF uses a built-in font, so characters outside basic Latin may not display correctly.

## License
MIT
