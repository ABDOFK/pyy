from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Tableau de bord
    path('', views.payment_dashboard, name='dashboard'),
    
    # Gestion des factures
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoice/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('create-invoice/<int:mission_id>/', views.create_invoice_from_mission, name='create_invoice'),
    
    # Processus de paiement
    path('pay/<int:pk>/', views.payment_page, name='payment_page'),
    path('pay/<int:pk>/success/', views.payment_success, name='payment_success'),
    path('pay/<int:pk>/cancel/', views.payment_cancel, name='payment_cancel'),
    
    # Méthodes de paiement spécifiques
    path('bank-transfer/<int:pk>/', views.bank_transfer_payment, name='bank_transfer'),
    path('escrow/<int:pk>/', views.escrow_payment, name='escrow_payment'),
    path('escrow/<int:pk>/release/', views.release_escrow, name='release_escrow'),
]