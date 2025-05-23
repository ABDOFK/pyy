from django.db import models

from django.db import models
from django.contrib.auth.models import User # Importe le modèle User intégré de Django
from django.db.models.signals import post_save # Signal pour créer le profil automatiquement
from django.dispatch import receiver # Décorateur pour connecter le signal

# Modèle pour stocker les informations spécifiques aux Freelances
class FreelanceProfile(models.Model):
    # Lien OneToOne: Chaque User ne peut avoir qu'un seul profil Freelance (ou aucun)
    # on_delete=models.CASCADE: Si le User est supprimé, son profil l'est aussi.
    # related_name: Permet d'accéder au profil depuis l'objet User (ex: user.freelance_profile)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='freelance_profile')

    # Champs spécifiques au Freelance (basés sur UML/Cahier des charges)
    titre_professionnel = models.CharField(max_length=200, blank=True, null=True, verbose_name="Titre Professionnel")
    competences = models.TextField(blank=True, null=True, verbose_name="Compétences") # Pourrait être ManyToManyField plus tard
    experience = models.TextField(blank=True, null=True, verbose_name="Expérience") # Pourrait être plus structuré plus tard
    portfolio_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="Lien Portfolio")
    taux_journalier = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Taux Journalier Moyen (€)")
    disponibilite = models.CharField(max_length=100, blank=True, null=True, verbose_name="Disponibilité") # Ex: "Immédiate", "Sous 2 semaines"
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    # Ajoutez d'autres champs si nécessaire (ex: photo de profil -> ImageField)

    def __str__(self):
        return f"Profil Freelance pour {self.user.username}"

    class Meta:
        verbose_name = "Profil Freelance"
        verbose_name_plural = "Profils Freelance"

# Modèle pour stocker les informations spécifiques aux Clients
class ClientProfile(models.Model):
    # Lien OneToOne similaire au profil Freelance
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')

    # Champs spécifiques au Client
    nom_entreprise = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom de l'entreprise")
    description_entreprise = models.TextField(blank=True, null=True, verbose_name="Description de l'entreprise")
    site_web_entreprise = models.URLField(max_length=200, blank=True, null=True, verbose_name="Site Web")
    adresse_entreprise = models.TextField(blank=True, null=True, verbose_name="Adresse de l'entreprise")
    telephone_entreprise = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone de l'entreprise")
    # Ajoutez d'autres champs si nécessaire

    def __str__(self):
        return f"Profil Client pour {self.user.username}"

    class Meta:
        verbose_name = "Profil Client"
        verbose_name_plural = "Profils Client"


# --- Optionnel mais pratique : Créer automatiquement un profil vide lors de la création d'un User ---
# On pourrait décider plus tard de quel type de profil créer (ou laisser l'utilisateur choisir)
# Pour l'instant, ce code ne crée PAS de profil automatiquement.
# On le fera manuellement ou lors de l'inscription spécifique.

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         # Décider ici si on crée un profil Freelance ou Client par défaut, ou rien
#         # Exemple: Ne rien faire par défaut
#         pass

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     # Si on avait créé un profil, il faudrait le sauvegarder
#     # Exemple:
#     # if hasattr(instance, 'freelance_profile'):
#     #     instance.freelance_profile.save()
#     # if hasattr(instance, 'client_profile'):
#     #     instance.client_profile.save()
#     pass
