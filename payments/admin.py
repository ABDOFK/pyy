from django.contrib import admin
from .models import Facture, Paiement

# Enregistrement simple
admin.site.register(Facture)
admin.site.register(Paiement)

# ----- Optionnel : Personnalisation -----
# class FactureAdmin(admin.ModelAdmin):
#     list_display = ('reference_facture', 'client', 'freelance', 'mission', 'montant_ttc', 'statut', 'date_emission', 'date_echeance')
#     list_filter = ('statut', 'date_emission', 'date_echeance')
#     search_fields = ('reference_facture', 'client__username', 'freelance__username', 'mission__titre')
#     readonly_fields = ('montant_ttc', 'date_emission') # Si calculé ou auto

# class PaiementAdmin(admin.ModelAdmin):
#     list_display = ('facture', 'montant', 'statut', 'date_paiement', 'methode_paiement')
#     list_filter = ('statut', 'date_paiement', 'methode_paiement')
#     search_fields = ('facture__reference_facture', 'reference_transaction')
#     readonly_fields = ('date_paiement',)

# admin.site.register(Facture, FactureAdmin)
# admin.site.register(Paiement, PaiementAdmin)