from django.urls import path
from . import views

urlpatterns = [
    path('apply/', views.apply_loan, name='apply_loan'),
    path('', views.loan_list, name='loan_list'),
    path('<int:pk>/', views.loan_detail, name='loan_detail'),
    path('<int:pk>/repay/', views.record_repayment, name='record_repayment'),
]
