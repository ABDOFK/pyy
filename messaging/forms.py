# messaging/forms.py
from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['contenu'] # Seulement le champ pour écrire le message
        widgets = {
            # Utiliser une textarea plus petite pour un chat
            'contenu': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Écrivez votre message ici...',
                'class': 'message-input' # Classe CSS pour le style
            }),
        }
        labels = {
            'contenu': '', # Pas besoin de label visible explicite pour un chat
        }