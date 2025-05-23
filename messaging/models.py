from django.db import models
from django.conf import settings

class Conversation(models.Model):
    # Permet des conversations de groupe, mais pour du 1-1 on s'assurera qu'il n'y a que 2 participants via la logique métier
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name="Participants"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_derniere_activite = models.DateTimeField(auto_now=True, verbose_name="Dernière activité") # Mis à jour à chaque nouveau message

    def __str__(self):
        usernames = ", ".join([user.username for user in self.participants.all()])
        # Limiter la longueur si trop de participants
        if len(usernames) > 50:
            usernames = usernames[:47] + "..."
        return f"Conversation entre {usernames}"

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-date_derniere_activite']

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE, # Si la conversation est supprimée, les messages aussi
        related_name='messages',
        verbose_name="Conversation"
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # Si l'auteur est supprimé, ses messages aussi (ou SET_NULL ?)
        related_name='messages_envoyes',
        verbose_name="Auteur"
    )
    contenu = models.TextField(verbose_name="Contenu du message")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date et heure d'envoi")
    # Pour une gestion simple du statut "lu" (pourrait être plus complexe avec ManyToMany pour les groupes)
    # lu_par = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='messages_lus', blank=True)

    def __str__(self):
        return f"Message de {self.auteur.username} à {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['timestamp'] # Ordonner les messages du plus ancien au plus récent dans une conversation