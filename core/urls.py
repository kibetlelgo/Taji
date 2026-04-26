from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('members/', views.member_list, name='member_list'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/<int:pk>/activate/', views.activate_member, name='activate_member'),
    path('members/<int:pk>/statement/', views.member_statement, name='member_statement'),
    path('savings/record/', views.record_savings, name='record_savings'),
    path('savings/add/', views.add_savings, name='add_savings'),
    path('sms/', views.send_sms_view, name='send_sms'),
    path('pay-registration/', views.pay_registration_fee, name='pay_registration'),
    path('registration-payments/', views.admin_registration_payments, name='admin_registration_payments'),
    path('registration-payments/<int:pk>/review/', views.approve_registration_payment, name='approve_registration_payment'),
    path('guarantors/', views.guarantors, name='guarantors'),
    path('recovery-log/', views.recovery_log, name='recovery_log'),
    path('loan-checker/', views.loan_checker, name='loan_checker'),
    path('admin-statements/', views.admin_statements, name='admin_statements'),
]
