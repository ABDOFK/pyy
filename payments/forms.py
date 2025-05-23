from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import Facture, PaymentMethod, FactureStatus

class FactureForm(forms.ModelForm):
    """Formulaire de création de facture"""
    
    date_echeance = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date d'échéance"
    )
    
    class Meta:
        model = Facture
        fields = [
            'montant_ht',
            'tva_taux',
            'date_echeance',
            'notes',
            'commission_taux'
        ]
        widgets = {
            'montant_ht': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'tva_taux': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.00',
                'max': '100.00',
                'placeholder': '20.00'
            }),
            'commission_taux': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.00',
                'max': '50.00',
                'placeholder': '5.00'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Notes additionnelles sur la facture...'
            }),
        }
        labels = {
            'montant_ht': 'Montant HT (€)',
            'tva_taux': 'Taux TVA (%)',
            'commission_taux': 'Commission FreelanceHub (%)',
            'notes': 'Notes'
        }
        help_texts = {
            'tva_taux': 'Taux de TVA applicable (0% si non assujetti)',
            'commission_taux': 'Commission prélevée par FreelanceHub (défaut: 5%)',
        }

class PaymentMethodForm(forms.Form):
    """Formulaire de sélection de méthode de paiement"""
    
    PAYMENT_CHOICES = [
        ('STRIPE', '💳 Carte bancaire (Stripe)'),
        ('PAYPAL', '🅿️ PayPal'),
        ('ESCROW', '🔒 Séquestre FreelanceHub'),
        ('BANK_TRANSFER', '🏦 Virement bancaire'),
    ]
    
    method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'}),
        label="Choisissez votre méthode de paiement"
    )
    
    accept_terms = forms.BooleanField(
        required=True,
        label="J'accepte les conditions générales de vente",
        widget=forms.CheckboxInput(attrs={'class': 'terms-checkbox'})
    )

class QuickInvoiceForm(forms.Form):
    """Formulaire rapide pour créer une facture depuis une mission"""
    
    montant_ht = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00',
            'class': 'amount-input'
        }),
        label="Montant HT (€)"
    )
    
    tva_taux = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=20.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0.00',
            'max': '100.00',
            'placeholder': '20.00'
        }),
        label="Taux TVA (%)"
    )
    
    date_echeance = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date d'échéance"
    )
    
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Description des prestations facturées...'
        }),
        label="Description"
    )
    
    def __init__(self, *args, mission=None, **kwargs):
        super().__init__(*args, **kwargs)
        if mission and mission.budget_propose:
            self.fields['montant_ht'].initial = mission.budget_propose

class BankTransferForm(forms.Form):
    """Formulaire pour paiement par virement bancaire"""
    
    bank_name = forms.CharField(
        max_length=100,
        label="Nom de votre banque",
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Crédit Agricole, BNP Paribas...'
        })
    )
    
    transfer_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date du virement"
    )
    
    transfer_reference = forms.CharField(
        max_length=100,
        label="Référence du virement",
        help_text="Référence fournie par votre banque",
        widget=forms.TextInput(attrs={
            'placeholder': 'Référence bancaire...'
        })
    )
    
    proof_of_payment = forms.FileField(
        required=False,
        label="Justificatif de paiement",
        help_text="Screenshot ou PDF du virement (optionnel)",
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.jpg,.jpeg,.png',
            'class': 'file-input'
        })
    )

class RefundRequestForm(forms.Form):
    """Formulaire de demande de remboursement"""
    
    REFUND_REASONS = [
        ('CANCEL', 'Annulation de la mission'),
        ('DISPUTE', 'Litige avec le freelance'),
        ('ERROR', 'Erreur de paiement'),
        ('DUPLICATE', 'Paiement en double'),
        ('OTHER', 'Autre raison'),
    ]
    
    reason = forms.ChoiceField(
        choices=REFUND_REASONS,
        label="Motif du remboursement",
        widget=forms.Select(attrs={'class': 'refund-reason-select'})
    )
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        label="Montant à rembourser (€)",
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        })
    )
    
    explanation = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Expliquez en détail les raisons de votre demande...'
        }),
        label="Explication détaillée"
    )
    
    supporting_documents = forms.FileField(
        required=False,
        label="Document justificatif",
        help_text="PDF, image ou autre document à l'appui",
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx',
            'class': 'file-input'
        })
    )

class EscrowReleaseForm(forms.Form):
    """Formulaire de libération des fonds du séquestre"""
    
    confirmation = forms.BooleanField(
        required=True,
        label="Je confirme que les prestations ont été réalisées de manière satisfaisante",
        widget=forms.CheckboxInput(attrs={'class': 'confirmation-checkbox'})
    )
    
    rating = forms.ChoiceField(
        choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)],
        required=False,
        label="Évaluation du freelance",
        widget=forms.RadioSelect(attrs={'class': 'rating-radio'})
    )
    
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Commentaire sur la prestation (optionnel)...'
        }),
        label="Commentaire"
    )

class PaymentFilterForm(forms.Form):
    """Formulaire de filtrage des paiements"""
    
    STATUS_CHOICES = [('', 'Tous les statuts')] + list(FactureStatus.choices)
    METHOD_CHOICES = [('', 'Toutes les méthodes')] + list(PaymentMethod.choices)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="Statut"
    )
    
    method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        required=False,
        label="Méthode de paiement"
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Du"
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Au"
    )
    
    min_amount = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0.00',
            'placeholder': '0.00'
        }),
        label="Montant minimum (€)"
    )
    
    max_amount = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0.00',
            'placeholder': '0.00'
        }),
        label="Montant maximum (€)"
    )