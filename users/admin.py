from django.contrib import admin
from .models import FreelanceProfile, ClientProfile # Importez vos modèles

# Enregistrement simple (affiche les modèles dans l'admin avec les champs par défaut)
admin.site.register(FreelanceProfile)
admin.site.register(ClientProfile)

# ----- Optionnel : Personnalisation de l'affichage dans l'Admin -----
# Si vous voulez personnaliser comment les modèles apparaissent dans l'admin
# (quels champs afficher dans la liste, ajouter des filtres, etc.),
# vous pouvez créer des classes ModelAdmin dédiées. Exemple :

# class FreelanceProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'titre_professionnel', 'taux_journalier', 'disponibilite') # Champs à afficher dans la liste
#     search_fields = ('user__username', 'titre_professionnel', 'competences') # Champs sur lesquels on peut rechercher
#     list_filter = ('disponibilite',) # Ajoute un filtre sur la disponibilité

# class ClientProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'nom_entreprise', 'site_web_entreprise')
#     search_fields = ('user__username', 'nom_entreprise')

# # Ensuite, enregistrez avec la classe personnalisée au lieu de l'enregistrement simple :
# # admin.site.register(FreelanceProfile, FreelanceProfileAdmin)
# # admin.site.register(ClientProfile, ClientProfileAdmin)

# Pour l'instant, l'enregistrement simple est suffisant.