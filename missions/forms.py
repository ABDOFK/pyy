# missions/forms.py
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import (Mission, Candidature, Evaluation, MissionProgress, 
                    MissionMilestone, MissionComment, MissionStatusUpdate, 
                    MissionStatus)  # Ajout de MissionStatus

class MissionForm(forms.ModelForm):
    # Utiliser des widgets pour améliorer l'interface
    date_limite_candidature = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False, # Rendre optionnel si besoin
        label="Date limite pour postuler"
    )
    date_debut_souhaitee = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="Date de début souhaitée"
    )
    date_fin_souhaitee = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="Date de fin souhaitée"
    )
    class Meta:
        model = Mission
        # Inclure les champs que le client doit remplir
        fields = [
            'titre',
            'description',
            'competences_requises',
            'budget_propose',
            'duree_estimee',
            'date_limite_candidature',
            'date_debut_souhaitee',
            'date_fin_souhaitee',
        ]
        # Exclure les champs gérés automatiquement ou plus tard
        # exclude = ('client', 'statut', 'freelance_assigne', 'date_publication') # Alternative à fields
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'competences_requises': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'budget_propose': "Budget proposé (€) (Optionnel)",
            'duree_estimee': "Durée estimée (ex: 3 semaines, 2 mois) (Optionnel)",
        }
        help_texts = {
            'competences_requises': "Listez les compétences clés, séparées par des virgules ou des sauts de ligne.",
        }

class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        # Champs que le freelance remplit en postulant
        fields = ['lettre_motivation', 'proposition_tarifaire']
        widgets = {
            'lettre_motivation': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Expliquez pourquoi vous êtes le bon candidat pour cette mission...'
            }),
        }
        labels = {
            'lettre_motivation': "Message / Lettre de motivation",
            'proposition_tarifaire': "Votre proposition tarifaire (€) (Optionnel)",
        }
        help_texts = {
             'proposition_tarifaire': "Laissez vide si vous acceptez le budget proposé ou pour discuter.",
        }

class EvaluationForm(forms.ModelForm):
    # Personnaliser le champ 'note' pour qu'il soit plus convivial
    # (par exemple, des boutons radio ou un select au lieu d'un simple champ nombre)
    CHOIX_NOTES = [(i, str(i)) for i in range(1, 6)] # Crée des tuples (1, '1'), (2, '2'), ..., (5, '5')

    note = forms.ChoiceField(
        choices=CHOIX_NOTES,
        widget=forms.RadioSelect, # Affiche des boutons radio
        label="Votre note (1 = Mauvais, 5 = Excellent)"
    )

    class Meta:
        model = Evaluation
        # Champs que l'utilisateur remplit pour évaluer
        fields = ['note', 'commentaire']
        # Exclure les champs qui seront définis automatiquement dans la vue:
        # 'mission', 'evaluateur', 'evalue'
        widgets = {
            'commentaire': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Partagez votre expérience détaillée ici...'
            }),
        }
        labels = {
            'commentaire': "Votre commentaire (Optionnel)",
        }

class MissionSearchForm(forms.Form):
    # Champ pour rechercher par mots-clés dans le titre ou la description
    keywords = forms.CharField(
        label="Mots-clés (titre, description)",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Python, Design Web, Rédaction'})
    )
    
    # Champ pour rechercher par compétences
    competences = forms.CharField(
        label="Compétences spécifiques",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Django, SEO, Photoshop'})
    )

class MissionProgressForm(forms.ModelForm):
    """Formulaire pour mettre à jour le pourcentage d'avancement"""
    class Meta:
        model = MissionProgress
        fields = ['pourcentage_completion', 'description_avancement']
        widgets = {
            'pourcentage_completion': forms.NumberInput(attrs={
                'min': '0',
                'max': '100',
                'step': '5',
                'class': 'progress-slider'
            }),
            'description_avancement': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Décrivez les progrès réalisés...'
            }),
        }
        labels = {
            'pourcentage_completion': 'Avancement (%)',
            'description_avancement': 'Description des progrès'
        }

class MissionStatusUpdateForm(forms.ModelForm):
    """Formulaire pour changer le statut d'une mission"""
    class Meta:
        model = MissionStatusUpdate
        fields = ['nouveau_statut', 'commentaire']
        widgets = {
            'nouveau_statut': forms.Select(attrs={'class': 'status-select'}),
            'commentaire': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Expliquez le changement de statut...'
            }),
        }
        labels = {
            'nouveau_statut': 'Nouveau statut',
            'commentaire': 'Commentaire (optionnel)'
        }

    def __init__(self, *args, current_status=None, user_role=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les statuts disponibles selon le rôle et le statut actuel
        if current_status and user_role:
            available_statuses = self.get_available_statuses(current_status, user_role)
            self.fields['nouveau_statut'].choices = [
                (status, label) for status, label in MissionStatus.choices
                if status in available_statuses
            ]

    def get_available_statuses(self, current_status, user_role):
        """Détermine les statuts disponibles selon le contexte"""
        transitions = {
            'client': {
                'OPEN': ['ASSIGNED', 'CANCELLED'],
                'ASSIGNED': ['IN_PROGRESS', 'CANCELLED'],
                'IN_PROGRESS': ['COMPLETED', 'CANCELLED'],
                'COMPLETED': ['CLOSED'],
            },
            'freelance': {
                'ASSIGNED': ['IN_PROGRESS'],
                'IN_PROGRESS': ['COMPLETED'],
            }
        }
        
        return transitions.get(user_role, {}).get(current_status, [])

class MissionMilestoneForm(forms.ModelForm):
    """Formulaire pour créer/modifier un jalon"""
    date_prevue = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date prévue"
    )
    
    class Meta:
        model = MissionMilestone
        fields = ['titre', 'description', 'date_prevue', 'ordre']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'ordre': forms.NumberInput(attrs={'min': '1', 'step': '1'}),
        }
        labels = {
            'titre': 'Titre du jalon',
            'description': 'Description (optionnel)',
            'ordre': 'Ordre d\'affichage'
        }

class MilestoneStatusForm(forms.Form):
    """Formulaire simple pour marquer un jalon comme complété"""
    est_complete = forms.BooleanField(
        required=False,
        label="Marquer comme complété"
    )
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label="Commentaire",
        help_text="Note sur la completion de cette étape"
    )

class MissionCommentForm(forms.ModelForm):
    """Formulaire pour ajouter un commentaire"""
    class Meta:
        model = MissionComment
        fields = ['contenu', 'est_prive']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Ajouter un commentaire...'
            }),
            'est_prive': forms.CheckboxInput(attrs={
                'class': 'private-checkbox'
            }),
        }
        labels = {
            'contenu': 'Commentaire',
            'est_prive': 'Commentaire privé (visible uniquement par moi)'
        }

class MissionTrackingFilterForm(forms.Form):
    """Formulaire de filtrage pour le tableau de bord"""
    STATUT_CHOICES = [('', 'Tous les statuts')] + list(MissionStatus.choices)
    
    statut = forms.ChoiceField(
        choices=STATUT_CHOICES,
        required=False,
        label="Filtrer par statut"
    )
    
    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="Depuis le"
    )
    
    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="Jusqu'au"
    )
    
    retard_uniquement = forms.BooleanField(
        required=False,
        label="Missions en retard uniquement"
    )