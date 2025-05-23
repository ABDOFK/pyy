# missions/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Mission, MissionStatus, Candidature, CandidatureStatus, Evaluation # Ajoutez Evaluation
from .forms import MissionForm, CandidatureForm, EvaluationForm, MissionSearchForm # Ajoutez EvaluationForm
from .forms import MissionForm, CandidatureForm # Ajoutez CandidatureForm
from django.views.decorators.http import require_POST # Pour les actions de modification (Accept/Reject)
# messaging/views.py
# ... (autres imports) ...
from django.contrib.auth import get_user_model # Pour récupérer le modèle User
from django.db.models import Count # Pour compter les participants

User = get_user_model() # Obtenir le modèle User actif

@login_required # Simple protection, tout utilisateur connecté peut voir
def mission_list_view(request):
    """Affiche la liste des missions ouvertes."""
    missions_ouvertes = Mission.objects.filter(statut=MissionStatus.OPEN).order_by('-date_publication')
    context = {
        'missions': missions_ouvertes,
    }
    return render(request, 'missions/mission_list.html', context)
    # Récupérer toutes les missions ouvertes initialement
    queryset = Mission.objects.filter(statut=MissionStatus.OPEN).order_by('-date_publication')
     # Initialiser le formulaire de recherche
    form = MissionSearchForm(request.GET or None) # request.GET pour pré-remplir si des filtres sont déjà appliqués

    if form.is_valid():
        print("Form is valid!")
        keywords = form.cleaned_data.get('keywords')
        competences = form.cleaned_data.get('competences')
        print(f"Keywords récupérés: '{keywords}'")
        print(f"Compétences récupérées: '{competences}'")
    else:
        print("Form is NOT valid. Errors:")
        print(form.errors)

        if keywords:
            # Recherche dans le titre OU la description (insensible à la casse)
            # Le Q object permet des conditions OR
            queryset = queryset.filter(
                Q(titre__icontains=keywords) | Q(description__icontains=keywords)
            )
        
        if competences:
            # Recherche simple dans le champ competences_requises
            # Pour une recherche plus avancée (ex: si compétences était un ManyToManyField),
            # la logique serait différente.
            # On peut rechercher plusieurs compétences séparées par des virgules par exemple.
            competences_list = [comp.strip() for comp in competences.split(',') if comp.strip()]
            for comp_item in competences_list:
                queryset = queryset.filter(competences_requises__icontains=comp_item)
        
        # Exemple pour budget (si vous ajoutez ces champs au formulaire)
        # if budget_min:
        #     queryset = queryset.filter(budget_propose__gte=budget_min)
        # if budget_max:
        #     queryset = queryset.filter(budget_propose__lte=budget_max)

    context = {
        'missions': queryset,
        'search_form': form,
    }
    return render(request, 'missions/mission_list.html', context)

# missions/views.py

@login_required
def mission_detail_view(request, pk):
    """Affiche les détails d'une mission spécifique."""
    mission = get_object_or_404(Mission, pk=pk)

    # --- AJOUTEZ CECI ---
    existing_candidature = None
    if request.user.is_authenticated and request.user != mission.client:
        # Cherche si l'utilisateur connecté a déjà postulé à CETTE mission
        existing_candidature = Candidature.objects.filter(mission=mission, freelance=request.user).first()
    # --- FIN DE L'AJOUT ---

    context = {
        'mission': mission,
        # --- AJOUTEZ existing_candidature AU CONTEXTE ---
        'existing_candidature': existing_candidature,
    }
    return render(request, 'missions/mission_detail.html', context)

@login_required
def create_mission_view(request):
    """Permet à un utilisateur connecté de créer une mission."""
    # Idéalement, vérifier si l'utilisateur est un client
    # if not hasattr(request.user, 'client_profile') or not request.user.client_profile:
    #     messages.error(request, "Vous devez avoir un profil Client pour publier une mission.")
    #     return redirect('home') # Ou vers la création de profil client

    if request.method == 'POST':
        form = MissionForm(request.POST)
        if form.is_valid():
            mission = form.save(commit=False)
            mission.client = request.user # Assigne l'utilisateur connecté comme client
            # Le statut par défaut est déjà 'OPEN' dans le modèle
            mission.save()
            messages.success(request, "Nouvelle mission publiée avec succès !")
            return redirect('missions:detail', pk=mission.pk) # Redirige vers la page détail de la nouvelle mission
        else:
            messages.error(request, "Erreur lors de la publication de la mission. Veuillez corriger les erreurs.")
    else: # GET
        form = MissionForm()

    context = {
        'form': form,
        'is_creation': True # Variable pour ajuster le titre/bouton dans le template
    }
    # Utilisation d'un template générique pour le formulaire
    return render(request, 'missions/mission_form.html', context)

@login_required
def my_missions_view(request):
    """Affiche les missions publiées par l'utilisateur connecté."""
    missions_utilisateur = Mission.objects.filter(client=request.user).order_by('-date_publication')
    context = {
        'missions': missions_utilisateur,
    }
    return render(request, 'missions/my_missions.html', context)

# Ajouter plus tard: vue pour modifier une mission (nécessite permission), vue pour postuler, etc.
# missions/views.py
# ... (vues existantes) ...

@login_required
def apply_to_mission_view(request, mission_pk):
    """Permet à un freelance de postuler à une mission."""
    mission = get_object_or_404(Mission, pk=mission_pk)

    # Vérifications:
    # 1. La mission est-elle ouverte ?
    if mission.statut != MissionStatus.OPEN:
        messages.error(request, "Les candidatures pour cette mission sont closes.")
        return redirect('missions:detail', pk=mission.pk)
    # 2. L'utilisateur est-il le client ? (ne peut pas postuler à sa propre mission)
    if mission.client == request.user:
         messages.error(request, "Vous ne pouvez pas postuler à votre propre mission.")
         return redirect('missions:detail', pk=mission.pk)
    # 3. L'utilisateur a-t-il un profil freelance ? (à affiner si besoin)
    # if not hasattr(request.user, 'freelance_profile'):
    #    messages.error(request, "Vous devez avoir un profil Freelance pour postuler.")
    #    return redirect('missions:detail', pk=mission.pk)
    # 4. L'utilisateur a-t-il déjà postulé ?
    existing_candidature = Candidature.objects.filter(mission=mission, freelance=request.user).first()
    if existing_candidature:
         messages.warning(request, "Vous avez déjà postulé à cette mission.")
         return redirect('missions:detail', pk=mission.pk)

    if request.method == 'POST':
        form = CandidatureForm(request.POST)
        if form.is_valid():
            candidature = form.save(commit=False)
            candidature.mission = mission
            candidature.freelance = request.user
            # Statut par défaut est SUBMITTED
            candidature.save()
            messages.success(request, "Votre candidature a été envoyée avec succès !")
            return redirect('missions:detail', pk=mission.pk) # Ou vers 'mes candidatures'
        else:
             messages.error(request, "Erreur dans le formulaire de candidature.")
    else: # GET
        form = CandidatureForm()

    context = {
        'form': form,
        'mission': mission,
    }
    return render(request, 'missions/apply_form.html', context)

@login_required
def my_applications_view(request):
    """Affiche les candidatures envoyées par le freelance connecté."""
    candidatures = Candidature.objects.filter(freelance=request.user).order_by('-date_candidature')
    context = {
        'candidatures': candidatures
    }
    return render(request, 'missions/my_applications.html', context)

@login_required
def view_candidatures_view(request, mission_pk):
    """Affiche les candidatures reçues pour une mission spécifique (pour le client)."""
    mission = get_object_or_404(Mission, pk=mission_pk)

    # Vérifier que l'utilisateur connecté est bien le client de la mission
    if mission.client != request.user:
        # messages.error(request, "Vous n'avez pas la permission de voir ces candidatures.")
        # return redirect('missions:detail', pk=mission.pk)
        # Ou mieux, une erreur Forbidden
        return HttpResponseForbidden("Vous n'êtes pas autorisé à accéder à cette page.")

    candidatures = mission.candidatures.all().order_by('-date_candidature') # Utilise le related_name

    context = {
        'mission': mission,
        'candidatures': candidatures,
    }
    return render(request, 'missions/candidature_list.html', context)


@login_required
@require_POST # S'assurer que cette vue ne peut être appelée qu'en POST
def accept_candidature_view(request, candidature_pk):
    """Action pour accepter une candidature (par le client)."""
    candidature = get_object_or_404(Candidature, pk=candidature_pk)
    mission = candidature.mission

    # Vérifier que l'utilisateur connecté est bien le client de la mission
    if mission.client != request.user:
        return HttpResponseForbidden("Action non autorisée.")

    # Vérifier si on peut accepter (mission ouverte, candidature soumise)
    if mission.statut == MissionStatus.OPEN and candidature.statut == CandidatureStatus.SUBMITTED:
        # Accepter la candidature
        candidature.statut = CandidatureStatus.ACCEPTED
        candidature.save()

        # Assigner le freelance et changer statut mission
        mission.freelance_assigne = candidature.freelance
        mission.statut = MissionStatus.ASSIGNED
        mission.save()

        # Optionnel: Refuser automatiquement les autres candidatures pour cette mission
        autres_candidatures = mission.candidatures.filter(statut=CandidatureStatus.SUBMITTED)
        autres_candidatures.update(statut=CandidatureStatus.REJECTED)

        messages.success(request, f"Candidature de {candidature.freelance.username} acceptée ! La mission est maintenant assignée.")
        # Envoyer notifications ici si nécessaire...
    else:
        messages.error(request, "Impossible d'accepter cette candidature (statut invalide).")

    # Rediriger vers la liste des candidatures de cette mission
    return redirect('missions:view_candidatures', mission_pk=mission.pk)

@login_required
@require_POST
def reject_candidature_view(request, candidature_pk):
    """Action pour refuser une candidature (par le client)."""
    candidature = get_object_or_404(Candidature, pk=candidature_pk)
    mission = candidature.mission

    # Vérifier que l'utilisateur connecté est bien le client de la mission
    if mission.client != request.user:
        return HttpResponseForbidden("Action non autorisée.")

    # Vérifier si on peut refuser (candidature soumise)
    if candidature.statut == CandidatureStatus.SUBMITTED:
        candidature.statut = CandidatureStatus.REJECTED
        candidature.save()
        messages.info(request, f"Candidature de {candidature.freelance.username} refusée.")
        # Envoyer notifications ici si nécessaire...
    else:
        messages.warning(request, "Cette candidature n'est plus en attente.")

    # Rediriger vers la liste des candidatures de cette mission
    return redirect('missions:view_candidatures', mission_pk=mission.pk)
# messaging/views.py
# ... (autres vues) ...

@login_required
def start_conversation_view(request, user_pk):
    """Trouve ou crée une conversation 1-1 avec un autre utilisateur."""
    target_user = get_object_or_404(User, pk=user_pk)
    current_user = request.user

    # Empêcher de démarrer une conversation avec soi-même
    if target_user == current_user:
        messages.warning(request, "Vous ne pouvez pas démarrer une conversation avec vous-même.")
        # Rediriger vers une page appropriée, ex: la liste des conversations ou le profil
        return redirect('messaging:list')

    # Chercher une conversation existante *uniquement* entre ces deux utilisateurs
    # On utilise annotate pour compter les participants et s'assurer qu'il y en a exactement 2
    conversation = Conversation.objects.annotate(
        num_participants=Count('participants')
    ).filter(
        participants=current_user
    ).filter(
        participants=target_user
    ).filter(
        num_participants=2
    ).first() # Prend la première trouvée s'il y en a

    # Si aucune conversation 1-1 n'existe, on en crée une nouvelle
    if conversation is None:
        conversation = Conversation.objects.create()
        conversation.participants.add(current_user, target_user)
        # Pas besoin de save() après .add() pour ManyToMany si l'objet principal existe déjà
        messages.success(request, f"Nouvelle conversation démarrée avec {target_user.username}.")

    # Rediriger vers la page détail de la conversation (existante ou nouvelle)
    return redirect('messaging:detail', pk=conversation.pk)

@login_required
def leave_evaluation_view(request, mission_pk):
    mission = get_object_or_404(Mission, pk=mission_pk)
    user = request.user

    # Déterminer qui est l'évaluateur et qui est l'évalué
    # C'est ici que la logique de qui peut évaluer qui pour une mission se précise.
    # Simplifions : si l'utilisateur est le client, il évalue le freelance assigné.
    # Si l'utilisateur est le freelance assigné, il évalue le client.

    evaluateur = user
    evalue = None

    if user == mission.client and mission.freelance_assigne:
        evalue = mission.freelance_assigne
    elif user == mission.freelance_assigne:
        evalue = mission.client
    else:
        # L'utilisateur n'est ni le client ni le freelance assigné, ou le freelance n'est pas encore assigné
        messages.error(request, "Vous ne pouvez pas évaluer cette mission dans son état actuel ou vous n'êtes pas concerné.")
        return redirect('missions:detail', pk=mission.pk)

    # Vérifier si une évaluation existe déjà par cet évaluateur pour cette mission
    # En utilisant unique_together = ('mission', 'evaluateur') dans le modèle Evaluation
    existing_evaluation = Evaluation.objects.filter(mission=mission, evaluateur=evaluateur).first()
    if existing_evaluation:
        messages.warning(request, f"Vous avez déjà évalué {evalue.username} pour cette mission.")
        # Optionnel: rediriger vers une vue pour modifier l'évaluation existante ?
        # Pour l'instant, on bloque une nouvelle évaluation.
        return redirect('missions:detail', pk=mission.pk)

    # Vérifier si la mission est dans un statut où l'évaluation est pertinente
    # Par exemple, seulement si la mission est 'COMPLETED' ou 'CLOSED'
    # if mission.statut not in [MissionStatus.COMPLETED, MissionStatus.CLOSED]:
    #     messages.info(request, "L'évaluation pour cette mission n'est pas encore disponible.")
    #     return redirect('missions:detail', pk=mission.pk)

    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.mission = mission
            evaluation.evaluateur = evaluateur
            evaluation.evalue = evalue
            evaluation.save()
            messages.success(request, f"Merci ! Votre évaluation pour {evalue.username} a été enregistrée.")
            return redirect('missions:detail', pk=mission.pk) # Ou vers la page de profil de l'évalué
        else:
            messages.error(request, "Erreur dans le formulaire d'évaluation. Veuillez corriger.")
    else: # GET
        form = EvaluationForm()

    context = {
        'form': form,
        'mission': mission,
        'person_to_evaluate': evalue, # Pour afficher à qui s'adresse l'évaluation
    }
    return render(request, 'missions/evaluation_form.html', context)