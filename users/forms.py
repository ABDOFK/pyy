# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    # Ajout de champs supplémentaires au formulaire d'inscription par défaut
    email = forms.EmailField(required=True, help_text='Requis. Une adresse email valide.')
    first_name = forms.CharField(max_length=30, required=False, label="Prénom")
    last_name = forms.CharField(max_length=150, required=False, label="Nom de famille")

    class Meta(UserCreationForm.Meta):
        model = User
        # Inclure les champs par défaut + les nouveaux
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

class CustomAuthenticationForm(AuthenticationForm):
    # Optionnel: Si vous voulez personnaliser le formulaire de connexion
    # Par exemple, changer les labels
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}), label="Nom d'utilisateur ou Email") # Permettre l'email aussi nécessiterait une logique d'authentification customisée
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
    )
    # Si vous n'avez pas besoin de personnalisation, vous pouvez utiliser directement AuthenticationForm dans les vues.
    # users/forms.py
# ... (imports existants: forms, UserCreationForm, AuthenticationForm, User)
from .models import FreelanceProfile, ClientProfile # Ajoutez cet import

# ... (classes existantes: CustomUserCreationForm, CustomAuthenticationForm)

class FreelanceProfileForm(forms.ModelForm):
    class Meta:
        model = FreelanceProfile
        # Exclure le champ 'user' car il sera défini automatiquement à partir de l'utilisateur connecté
        exclude = ('user',)
        # Optionnel: Définir l'ordre des champs, les widgets, les labels, etc.
        # fields = ['titre_professionnel', 'competences', ...] # Alternative à exclude
        widgets = {
            'competences': forms.Textarea(attrs={'rows': 3}),
            'experience': forms.Textarea(attrs={'rows': 4}),
            'adresse': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'taux_journalier': "Taux Journalier Moyen (€)", # Répète verbose_name si besoin de le forcer ici
        }

class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        exclude = ('user',)
        widgets = {
            'description_entreprise': forms.Textarea(attrs={'rows': 4}),
            'adresse_entreprise': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'nom_entreprise': "Nom de l'entreprise (si applicable)",
        }


class FreelanceSearchForm(forms.Form):
    # Champ pour rechercher par mots-clés dans le titre professionnel ou l'expérience
    keywords = forms.CharField(
        label="Mots-clés (titre, expérience)",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Développeur web, Designer, Consultant'
        })
    )
    
    # Champ pour rechercher par compétences spécifiques
    competences = forms.CharField(
        label="Compétences recherchées",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Django, Photoshop, SEO, React'
        })
    )
    
    # Filtre par budget (taux journalier)
    taux_min = forms.DecimalField(
        label="Taux journalier minimum (€)",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': '0',
            'step': '50'
        })
    )
    
    taux_max = forms.DecimalField(
        label="Taux journalier maximum (€)",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': '1000',
            'step': '50'
        })
    )
    
    # Filtre par disponibilité
    DISPONIBILITE_CHOICES = [
        ('', 'Toutes'),
        ('Immédiate', 'Disponible immédiatement'),
        ('Sous 1 semaine', 'Sous 1 semaine'),
        ('Sous 2 semaines', 'Sous 2 semaines'),
        ('Sous 1 mois', 'Sous 1 mois'),
    ]
    
    disponibilite = forms.ChoiceField(
        label="Disponibilité",
        choices=DISPONIBILITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )       