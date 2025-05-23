from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

def generate_invoice_reference():
    """Génère une référence de facture"""
    import datetime
    import random
    today = datetime.date.today()
    random_num = random.randint(1000, 9999)
    return f"INV-{today.strftime('%Y%m%d')}-{random_num}"

def generate_payment_reference():
    """Génère une référence de paiement"""
    import datetime
    import random
    today = datetime.date.today()
    random_num = random.randint(1000, 9999)
    return f"PAY-{today.strftime('%Y%m%d')}-{random_num}"

# Choix pour le statut d'une facture
class FactureStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Brouillon'       
    SENT = 'SENT', 'Envoyée'         
    PAID = 'PAID', 'Payée'           
    OVERDUE = 'OVERDUE', 'En retard'     
    CANCELLED = 'CANCELLED', 'Annulée'   

# Choix pour le statut d'un paiement
class PaiementStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'   
    SUCCESS = 'SUCCESS', 'Réussi'       
    FAILED = 'FAILED', 'Échoué'       
    REFUNDED = 'REFUNDED', 'Remboursé'
    PROCESSING = 'PROCESSING', 'En cours de traitement'

# Choix pour les méthodes de paiement
class PaymentMethod(models.TextChoices):
    STRIPE = 'STRIPE', 'Carte bancaire (Stripe)'
    PAYPAL = 'PAYPAL', 'PayPal'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Virement bancaire'
    ESCROW = 'ESCROW', 'Séquestre FreelanceHub'

class Facture(models.Model):
    mission = models.ForeignKey(
        'missions.Mission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='factures',
        verbose_name="Mission associée"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='factures_recues',
        verbose_name="Client facturé"
    )
    freelance = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='factures_emises',
        verbose_name="Freelance émetteur"
    )
    
    # Identifiants
    reference_facture = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Référence unique",
        default=generate_invoice_reference
    )
    
    # Montants
    montant_ht = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Montant HT (€)",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    tva_taux = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Taux TVA (%)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    montant_ttc = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Montant TTC (€)",
        default=0.00
    )
    
    # Commission de la plateforme
    commission_taux = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        verbose_name="Taux de commission (%)",
        help_text="Commission de FreelanceHub"
    )
    commission_montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Montant de commission (€)"
    )
    montant_freelance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Montant pour le freelance (€)"
    )
    
    # Dates
    date_emission = models.DateTimeField(auto_now_add=True, verbose_name="Date d'émission")
    date_echeance = models.DateField(verbose_name="Date d'échéance")
    date_paiement = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement")
    
    # Statut et détails
    statut = models.CharField(
        max_length=20,
        choices=FactureStatus.choices,
        default=FactureStatus.DRAFT,
        verbose_name="Statut"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes / Détails")

    def save(self, *args, **kwargs):
        # Calculer le montant TTC
        if self.montant_ht and self.tva_taux is not None:
            self.montant_ttc = self.montant_ht * (1 + (self.tva_taux / 100))
        
        # Calculer la commission et le montant pour le freelance
        if self.montant_ttc:
            self.commission_montant = self.montant_ttc * (self.commission_taux / 100)
            self.montant_freelance = self.montant_ttc - self.commission_montant
        
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Vérifie si la facture est en retard"""
        if self.statut in [FactureStatus.PAID, FactureStatus.CANCELLED]:
            return False
        from django.utils import timezone
        return self.date_echeance < timezone.now().date()

    @property
    def can_be_paid(self):
        """Vérifie si la facture peut être payée"""
        return self.statut in [FactureStatus.SENT, FactureStatus.OVERDUE]

    def mark_as_paid(self):
        """Marque la facture comme payée"""
        from django.utils import timezone
        self.statut = FactureStatus.PAID
        self.date_paiement = timezone.now()
        self.save()

    def __str__(self):
        return f"Facture {self.reference_facture} - {self.montant_ttc}€"

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_emission']

class Paiement(models.Model):
    facture = models.ForeignKey(
        Facture,
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name="Facture concernée"
    )
    
    # Identifiants
    reference_paiement = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Référence paiement",
        default=generate_payment_reference
    )
    
    # Détails du paiement
    montant = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Montant payé (€)",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    methode_paiement = models.CharField(
        max_length=50,
        choices=PaymentMethod.choices,
        verbose_name="Méthode de paiement"
    )
    
    # Statut et dates
    statut = models.CharField(
        max_length=20,
        choices=PaiementStatus.choices,
        default=PaiementStatus.PENDING,
        verbose_name="Statut du paiement"
    )
    date_paiement = models.DateTimeField(auto_now_add=True, verbose_name="Date et heure du paiement")
    date_confirmation = models.DateTimeField(null=True, blank=True, verbose_name="Date de confirmation")

    def confirm_payment(self):
        """Confirme le paiement et met à jour la facture"""
        from django.utils import timezone
        self.statut = PaiementStatus.SUCCESS
        self.date_confirmation = timezone.now()
        self.save()
        
        # Marquer la facture comme payée si le montant correspond
        if self.montant >= self.facture.montant_ttc:
            self.facture.mark_as_paid()

    def __str__(self):
        return f"Paiement {self.reference_paiement} - {self.montant}€ ({self.get_statut_display()})"

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement']

class EscrowAccount(models.Model):
    """Compte de séquestre pour sécuriser les paiements"""
    facture = models.OneToOneField(
        Facture,
        on_delete=models.CASCADE,
        related_name='escrow_account',
        verbose_name="Facture"
    )
    montant_bloque = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant bloqué (€)"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_liberation = models.DateTimeField(null=True, blank=True, verbose_name="Date de libération")
    est_libere = models.BooleanField(default=False, verbose_name="Fonds libérés")
    
    class Meta:
        verbose_name = "Compte Séquestre"
        verbose_name_plural = "Comptes Séquestre"
        ordering = ['-date_creation']

    def __str__(self):
        return f"Séquestre {self.facture.reference_facture} - {self.montant_bloque}€"