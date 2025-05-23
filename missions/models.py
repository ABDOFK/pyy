from django.db import models
from django.conf import settings  # Pour lier aux Users (bonne pratique)

# from users.models import FreelanceProfile, ClientProfile # On lie plutôt au User directement
from django.core.validators import MinValueValidator, MaxValueValidator


# Choix possibles pour le statut d'une mission
class MissionStatus(models.TextChoices):
    OPEN = "OPEN", "Ouverte"  # Nouvelle mission, recherche de candidats
    ASSIGNED = "ASSIGNED", "Assignée"  # Un freelance a été choisi
    IN_PROGRESS = "IN_PROGRESS", "En cours"  # Travail démarré
    COMPLETED = (
        "COMPLETED",
        "Terminée",
    )  # Travail fini, en attente de validation/paiement
    CLOSED = "CLOSED", "Fermée"  # Mission terminée et payée/archivée
    CANCELLED = "CANCELLED", "Annulée"  # Mission annulée


# Choix possibles pour le statut d'une candidature
class CandidatureStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Envoyée"  # Le freelance a postulé
    VIEWED = "VIEWED", "Vue"  # Le client a vu la candidature
    ACCEPTED = "ACCEPTED", "Acceptée"  # Le client a choisi ce freelance
    REJECTED = "REJECTED", "Refusée"  # Le client n'a pas choisi ce freelance
    WITHDRAWN = "WITHDRAWN", "Retirée"  # Le freelance a annulé sa candidature


class Mission(models.Model):
    @property
    def completed_milestones_count(self):
        """Retourne le nombre de jalons complétés"""
        return self.milestones.filter(est_complete=True).count()

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # Si le client est supprimé, ses missions aussi
        related_name="missions_publiees",
        verbose_name="Client",
        # limit_choices_to={'client_profile__isnull': False} # Optionnel: Pour s'assurer que c'est bien un client
    )
    titre = models.CharField(max_length=255, verbose_name="Titre de la mission")
    description = models.TextField(verbose_name="Description détaillée")
    competences_requises = models.TextField(
        blank=True, null=True, verbose_name="Compétences requises"
    )  # Ou ManyToMany vers un modèle Skill
    budget_propose = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Budget proposé (€)",
    )
    duree_estimee = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Durée estimée"
    )  # Ex: "2 semaines", "1 mois"
    date_publication = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de publication"
    )  # Se met automatiquement à la création
    date_limite_candidature = models.DateField(
        blank=True, null=True, verbose_name="Date limite pour postuler"
    )
    date_debut_souhaitee = models.DateField(
        blank=True, null=True, verbose_name="Date de début souhaitée"
    )
    date_fin_souhaitee = models.DateField(
        blank=True, null=True, verbose_name="Date de fin souhaitée"
    )

    statut = models.CharField(
        max_length=20,
        choices=MissionStatus.choices,
        default=MissionStatus.OPEN,
        verbose_name="Statut",
    )

    freelance_assigne = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Si le freelance est supprimé, la mission n'est plus assignée mais existe toujours
        related_name="missions_assignees",
        blank=True,  # Non obligatoire (au début, pas de freelance assigné)
        null=True,  # Peut être vide en BDD
        verbose_name="Freelance Assigné",
        # limit_choices_to={'freelance_profile__isnull': False} # Optionnel: Pour s'assurer que c'est bien un freelance
    )

    def __str__(self):
        return f"{self.titre} (Client: {self.client.username})"

    class Meta:
        verbose_name = "Mission"
        verbose_name_plural = "Missions"
        ordering = [
            "-date_publication"
        ]  # Ordonner par défaut les missions de la plus récente à la plus ancienne


class Candidature(models.Model):
    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,  # Si la mission est supprimée, les candidatures aussi
        related_name="candidatures",
        verbose_name="Mission Concernée",
    )
    freelance = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # Si le freelance est supprimé, ses candidatures aussi
        related_name="mes_candidatures",
        verbose_name="Freelance Candidat",
        # limit_choices_to={'freelance_profile__isnull': False} # Optionnel
    )
    lettre_motivation = models.TextField(
        blank=True, null=True, verbose_name="Message / Lettre de motivation"
    )
    proposition_tarifaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Proposition tarifaire (€)",
    )  # Si applicable
    date_candidature = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de candidature"
    )

    statut = models.CharField(
        max_length=20,
        choices=CandidatureStatus.choices,
        default=CandidatureStatus.SUBMITTED,
        verbose_name="Statut",
    )

    def __str__(self):
        return f"Candidature de {self.freelance.username} pour {self.mission.titre}"

    class Meta:
        verbose_name = "Candidature"
        verbose_name_plural = "Candidatures"
        ordering = ["-date_candidature"]
        # Assurer qu'un freelance ne postule qu'une fois par mission
        unique_together = ("mission", "freelance")


class Evaluation(models.Model):
    mission = models.OneToOneField(  # Une mission ne devrait avoir qu'une évaluation par "sens" (Client->Freelance ou Freelance->Client)
        # Mais ici, on simplifie: une évaluation globale ou on précisera l'évaluateur/évalué
        Mission,
        on_delete=models.CASCADE,  # Si la mission est supprimée, l'évaluation aussi
        related_name="evaluation",  # Accès depuis la mission: mission.evaluation
        verbose_name="Mission Évaluée",
    )
    evaluateur = models.ForeignKey(  # L'utilisateur qui donne l'évaluation
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="evaluations_donnees",
        verbose_name="Évaluateur",
    )
    evalue = models.ForeignKey(  # L'utilisateur qui reçoit l'évaluation
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="evaluations_recues",
        verbose_name="Personne Évaluée",
    )
    note = models.PositiveSmallIntegerField(  # Note de 1 à 5 par exemple
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note (sur 5)",
    )
    commentaire = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    date_evaluation = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de l'évaluation"
    )

    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ["-date_evaluation"]
        # Assurer qu'un évaluateur ne peut donner qu'une évaluation pour une personne évaluée sur une mission donnée
        # S'il y a deux sens d'évaluation, il faudrait un champ "type_evaluation" (client_vers_freelance, freelance_vers_client)
        # Pour une évaluation "globale" de la mission par un des acteurs principaux :
        unique_together = (
            "mission",
            "evaluateur",
        )  # Un utilisateur ne peut évaluer une mission qu'une fois

    def __str__(self):
        return f"Évaluation de {self.evalue.username} par {self.evaluateur.username} pour {self.mission.titre} ({self.note}/5)"


# Ajoutez ces modèles à la fin de missions/models.py


class MissionStatusUpdate(models.Model):
    """Suivi des mises à jour de statut d'une mission"""

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name="status_updates",
        verbose_name="Mission",
    )
    ancien_statut = models.CharField(
        max_length=20, choices=MissionStatus.choices, verbose_name="Ancien statut"
    )
    nouveau_statut = models.CharField(
        max_length=20, choices=MissionStatus.choices, verbose_name="Nouveau statut"
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Auteur de la modification",
    )
    commentaire = models.TextField(blank=True, null=True, verbose_name="Commentaire")
    date_modification = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de modification"
    )

    class Meta:
        verbose_name = "Mise à jour de statut"
        verbose_name_plural = "Mises à jour de statut"
        ordering = ["-date_modification"]

    def __str__(self):
        return f"{self.mission.titre} : {self.ancien_statut} → {self.nouveau_statut}"


class MissionProgress(models.Model):
    """Suivi du pourcentage d'avancement d'une mission"""

    mission = models.OneToOneField(
        Mission,
        on_delete=models.CASCADE,
        related_name="progress",
        verbose_name="Mission",
    )
    pourcentage_completion = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Pourcentage de completion (%)",
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, verbose_name="Dernière mise à jour"
    )
    mise_a_jour_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Mis à jour par",
    )
    description_avancement = models.TextField(
        blank=True, null=True, verbose_name="Description de l'avancement"
    )

    class Meta:
        verbose_name = "Progression de mission"
        verbose_name_plural = "Progressions de mission"

    def __str__(self):
        return f"{self.mission.titre} - {self.pourcentage_completion}%"


class MissionMilestone(models.Model):
    """Jalons/étapes d'une mission"""

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name="milestones",
        verbose_name="Mission",
    )
    titre = models.CharField(max_length=200, verbose_name="Titre du jalon")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    date_prevue = models.DateField(verbose_name="Date prévue")
    date_completion = models.DateField(
        blank=True, null=True, verbose_name="Date de completion"
    )
    est_complete = models.BooleanField(default=False, verbose_name="Est complété")
    ordre = models.PositiveIntegerField(default=1, verbose_name="Ordre d'affichage")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Créé par"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )

    class Meta:
        verbose_name = "Jalon de mission"
        verbose_name_plural = "Jalons de mission"
        ordering = ["ordre", "date_prevue"]

    def __str__(self):
        status = "✓" if self.est_complete else "○"
        return f"{status} {self.titre}"

    @property
    def is_overdue(self):
        """Vérifie si le jalon est en retard"""
        if self.est_complete:
            return False
        from django.utils import timezone

        return self.date_prevue < timezone.now().date()


class MissionComment(models.Model):
    """Commentaires et notes sur une mission"""

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Mission",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Auteur"
    )
    contenu = models.TextField(verbose_name="Commentaire")
    est_prive = models.BooleanField(
        default=False,
        verbose_name="Commentaire privé",
        help_text="Visible uniquement par l'auteur",
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    date_modification = models.DateTimeField(
        auto_now=True, verbose_name="Date de modification"
    )

    class Meta:
        verbose_name = "Commentaire de mission"
        verbose_name_plural = "Commentaires de mission"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Commentaire de {self.auteur.username} sur {self.mission.titre}"
