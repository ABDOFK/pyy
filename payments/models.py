from django.db import models
from django.conf import settings
# from missions.models import Mission # On peut lier à la mission

# Choix pour le statut d'une facture
class FactureStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Brouillon'       # Facture en cours de création
    SENT = 'SENT', 'Envoyée'         # Facture envoyée au client
    PAID = 'PAID', 'Payée'           # Facture entièrement payée
    OVERDUE = 'OVERDUE', 'En retard'     # Date d'échéance dépassée et non payée
    CANCELLED = 'CANCELLED', 'Annulée'   # Facture annulée

# Choix pour le statut d'un paiement
class PaiementStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'   # Paiement initié mais pas encore confirmé
    SUCCESS = 'SUCCESS', 'Réussi'       # Paiement confirmé
    FAILED = 'FAILED', 'Échoué'       # Paiement échoué
    REFUNDED = 'REFUNDED', 'Remboursé'  # Paiement remboursé

class Facture(models.Model):
    # Lier à la mission est logique
    mission = models.ForeignKey(
        'missions.Mission', # Utilisation d'une chaîne pour éviter l'import circulaire direct
        on_delete=models.SET_NULL, # Si la mission est supprimée, on garde la facture mais sans lien direct
        null=True,
        blank=True, # Peut-être des factures hors mission ? Ou initialement pas liée ?
        related_name='factures',
        verbose_name="Mission associée"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT, # Empêcher la suppression du client si des factures existent
        related_name='factures_recues',
        verbose_name="Client facturé"
    )
    freelance = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT, # Empêcher la suppression du freelance si des factures existent
        related_name='factures_emises',
        verbose_name="Freelance émetteur"
    )
    reference_facture = models.CharField(max_length=100, unique=True, verbose_name="Référence unique") # Ex: INV-2025-001
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant HT (€)")
    tva_taux = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Taux TVA (%)") # Ex: 20.00 pour 20%
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant TTC (€)") # Calculé ou entré

    date_emission = models.DateField(auto_now_add=True, verbose_name="Date d'émission")
    date_echeance = models.DateField(verbose_name="Date d'échéance")

    statut = models.CharField(
        max_length=20,
        choices=FactureStatus.choices,
        default=FactureStatus.DRAFT,
        verbose_name="Statut"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes / Détails")

    # Pour le calcul automatique du TTC (si nécessaire)
    def save(self, *args, **kwargs):
        # Exemple simple de calcul TTC si HT et Taux sont présents
        if self.montant_ht and self.tva_taux is not None:
             self.montant_ttc = self.montant_ht * (1 + (self.tva_taux / 100))
        super().save(*args, **kwargs) # Appelle la méthode save originale

    def __str__(self):
        return f"Facture {self.reference_facture} pour {self.client.username}"

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_emission']

class Paiement(models.Model):
    facture = models.ForeignKey(
        Facture,
        on_delete=models.CASCADE, # Si la facture est supprimée, les paiements associés aussi
        related_name='paiements',
        verbose_name="Facture concernée"
    )
    # On pourrait aussi lier le client qui a payé, même si c'est implicite via la facture
    # client_payeur = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant payé (€)")
    date_paiement = models.DateTimeField(auto_now_add=True, verbose_name="Date et heure du paiement")
    methode_paiement = models.CharField(max_length=50, blank=True, null=True, verbose_name="Méthode de paiement") # Ex: Stripe, PayPal, Virement
    reference_transaction = models.CharField(max_length=255, blank=True, null=True, verbose_name="Référence transaction externe") # Ex: ID de transaction Stripe

    statut = models.CharField(
        max_length=20,
        choices=PaiementStatus.choices,
        default=PaiementStatus.PENDING,
        verbose_name="Statut du paiement"
    )
    # Pourrait être utile pour stocker les retours de la passerelle
    details_passerelle = models.JSONField(blank=True, null=True, verbose_name="Détails Passerelle (JSON)")

    def __str__(self):
        return f"Paiement de {self.montant}€ pour Facture {self.facture.reference_facture} ({self.statut})"

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement']