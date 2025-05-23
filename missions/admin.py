from django.contrib import admin
from .models import Mission, Candidature # Importez vos modèles
from .models import Mission, Candidature, Evaluation

# Enregistrement simple
admin.site.register(Mission)
admin.site.register(Candidature)

# ----- Optionnel : Personnalisation plus avancée -----
# Exemple de personnalisation pour Mission
# class MissionAdmin(admin.ModelAdmin):
#     list_display = ('titre', 'client', 'statut', 'freelance_assigne', 'date_publication', 'budget_propose')
#     list_filter = ('statut', 'date_publication')
#     search_fields = ('titre', 'description', 'client__username', 'freelance_assigne__username')
#     # Pour afficher les champs ForeignKey en lecture seule lors de l'édition
#     readonly_fields = ('date_publication',)
#     # Organiser les champs dans le formulaire d'édition
#     fieldsets = (
#         (None, {
#             'fields': ('titre', 'client', 'description', 'competences_requises')
#         }),
#         ('Détails & Délais', {
#             'fields': ('budget_propose', 'duree_estimee', 'date_limite_candidature', 'date_debut_souhaitee', 'date_fin_souhaitee')
#         }),
#         ('Statut & Assignation', {
#             'fields': ('statut', 'freelance_assigne', 'date_publication')
#         }),
#     )

# Exemple de personnalisation pour Candidature
# class CandidatureAdmin(admin.ModelAdmin):
#     list_display = ('mission', 'freelance', 'statut', 'date_candidature')
#     list_filter = ('statut', 'date_candidature')
#     search_fields = ('mission__titre', 'freelance__username', 'lettre_motivation')
#     readonly_fields = ('date_candidature',)


# Enregistrement avec personnalisation (décommenter si utilisé)
# admin.site.register(Mission, MissionAdmin)
# admin.site.register(Candidature, CandidatureAdmin)
# Exemple de personnalisation pour Evaluation (optionnel)
# class EvaluationAdmin(admin.ModelAdmin):
#     list_display = ('mission', 'evaluateur', 'evalue', 'note', 'date_evaluation')
#     list_filter = ('note', 'date_evaluation')
#     search_fields = ('mission__titre', 'evaluateur__username', 'evalue__username', 'commentaire')
#     readonly_fields = ('date_evaluation',)

# admin.site.register(Evaluation, EvaluationAdmin) # Si vous utilisez la personnalisation