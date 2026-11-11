from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_expense, name='add'),
    path('edit/<int:pk>/', views.edit_expense, name='edit'),
    path('delete/<int:pk>/', views.delete_expense, name='delete'),
    path('download/csv/', views.download_csv, name='csv'),
    path('download/pdf/', views.download_pdf, name='pdf'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
