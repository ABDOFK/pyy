# missions/forms.py
from django import forms
from .models import Mission, Candidature
from .models import Mission, Candidature, Evaluation

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

    # Optionnel: Ajouter de la validation personnalisée si nécessaire
    # def clean_budget_propose(self):
    #     budget = self.cleaned_data.get('budget_propose')
    #     if budget and budget < 0:
    #         raise forms.ValidationError("Le budget ne peut pas être négatif.")
    #     return budget

    
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

    # Optionnel: Validation supplémentaire si nécessaire
    # def clean_note(self):
    #     note = self.cleaned_data.get('note')
    #     # Django valide déjà MinValue/MaxValue via le modèle, mais on pourrait ajouter autre chose
    #     return note