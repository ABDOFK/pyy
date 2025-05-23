# messaging/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count # S'assurer que Count est ici
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from .forms import MessageForm

User = get_user_model()

@login_required
def conversation_list_view(request):
    """Affiche la liste des conversations de l'utilisateur."""
    # Récupère toutes les conversations où l'utilisateur est un participant
    conversations = request.user.conversations.all().order_by('-date_derniere_activite')
    context = {
        'conversations': conversations,
    }
    return render(request, 'messaging/conversation_list.html', context)

@login_required
def start_conversation_view(request, user_pk): # <--- VÉRIFIEZ L'ORTHOGRAPHE EXACTE ICI
    """Trouve ou crée une conversation 1-1 avec un autre utilisateur."""
    target_user = get_object_or_404(User, pk=user_pk)
    current_user = request.user

    if target_user == current_user:
        messages.warning(request, "Vous ne pouvez pas démarrer une conversation avec vous-même.")
        return redirect('messaging:list')

    conversation = Conversation.objects.annotate(
        num_participants=Count('participants')
    ).filter(
        participants=current_user
    ).filter(
        participants=target_user
    ).filter(
        num_participants=2
    ).first()

    if conversation is None:
        conversation = Conversation.objects.create()
        conversation.participants.add(current_user, target_user)
        messages.success(request, f"Nouvelle conversation démarrée avec {target_user.username}.")

    return redirect('messaging:detail', pk=conversation.pk)

@login_required
def conversation_detail_view(request, pk): # <--- VÉRIFIEZ L'ORTHOGRAPHE ET L'EXISTENCE DE CETTE FONCTION
    """Affiche une conversation spécifique et gère l'envoi de messages."""
    conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)
    messages_list = conversation.messages.all().order_by('timestamp')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.auteur = request.user
            message.save()
            conversation.date_derniere_activite = timezone.now()
            conversation.save(update_fields=['date_derniere_activite'])
            return redirect('messaging:detail', pk=conversation.pk)
    else: # GET
        form = MessageForm()

    context = {
        'conversation': conversation,
        'messages_list': messages_list,
        'form': form,
    }
    return render(request, 'messaging/conversation_detail.html', context)