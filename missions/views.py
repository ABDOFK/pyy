# missions/views.py
from django.template.loader import render_to_string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Mission, MissionStatus, Candidature, CandidatureStatus, Evaluation
from .forms import MissionForm, CandidatureForm, EvaluationForm, MissionSearchForm
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db.models import Count, Q  # Added Q import for search
from django.http import HttpResponseForbidden
from .models import (
    MissionProgress,
    MissionMilestone,
    MissionComment,
    MissionStatusUpdate,
)
from .forms import (
    MissionProgressForm,
    MissionStatusUpdateForm,
    MissionMilestoneForm,
    MilestoneStatusForm,
    MissionCommentForm,
    MissionTrackingFilterForm,
)

from django.utils import timezone
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
import json

User = get_user_model()


@login_required
def mission_list_view(request):
    """Affiche la liste des missions ouvertes avec recherche."""
    # Récupérer toutes les missions ouvertes initialement
    queryset = Mission.objects.filter(statut=MissionStatus.OPEN).order_by(
        "-date_publication"
    )

    # Initialiser le formulaire de recherche
    form = MissionSearchForm(request.GET or None)

    if form.is_valid():
        keywords = form.cleaned_data.get("keywords")
        competences = form.cleaned_data.get("competences")

        if keywords:
            # Recherche dans le titre OU la description (insensible à la casse)
            queryset = queryset.filter(
                Q(titre__icontains=keywords) | Q(description__icontains=keywords)
            )

        if competences:
            # Recherche simple dans le champ competences_requises
            competences_list = [
                comp.strip() for comp in competences.split(",") if comp.strip()
            ]
            for comp_item in competences_list:
                queryset = queryset.filter(competences_requises__icontains=comp_item)

    context = {
        "missions": queryset,
        "search_form": form,
    }
    return render(request, "missions/mission_list.html", context)


@login_required
def mission_detail_view(request, pk):
    """Affiche les détails d'une mission spécifique."""
    mission = get_object_or_404(Mission, pk=pk)

    existing_candidature = None
    if request.user.is_authenticated and request.user != mission.client:
        existing_candidature = Candidature.objects.filter(
            mission=mission, freelance=request.user
        ).first()

    context = {
        "mission": mission,
        "existing_candidature": existing_candidature,
    }
    return render(request, "missions/mission_detail.html", context)


@login_required
def create_mission_view(request):
    """Permet à un utilisateur connecté de créer une mission."""
    if request.method == "POST":
        form = MissionForm(request.POST)
        if form.is_valid():
            mission = form.save(commit=False)
            mission.client = request.user
            mission.save()
            messages.success(request, "Nouvelle mission publiée avec succès !")
            return redirect("missions:detail", pk=mission.pk)
        else:
            messages.error(
                request,
                "Erreur lors de la publication de la mission. Veuillez corriger les erreurs.",
            )
    else:
        form = MissionForm()

    context = {"form": form, "is_creation": True}
    return render(request, "missions/mission_form.html", context)


@login_required
def my_missions_view(request):
    """Affiche les missions publiées par l'utilisateur connecté."""
    missions_utilisateur = Mission.objects.filter(client=request.user).order_by(
        "-date_publication"
    )
    context = {
        "missions": missions_utilisateur,
    }
    return render(request, "missions/my_missions.html", context)


@login_required
def apply_to_mission_view(request, mission_pk):
    """Permet à un freelance de postuler à une mission."""
    mission = get_object_or_404(Mission, pk=mission_pk)

    if mission.statut != MissionStatus.OPEN:
        messages.error(request, "Les candidatures pour cette mission sont closes.")
        return redirect("missions:detail", pk=mission.pk)

    if mission.client == request.user:
        messages.error(request, "Vous ne pouvez pas postuler à votre propre mission.")
        return redirect("missions:detail", pk=mission.pk)

    existing_candidature = Candidature.objects.filter(
        mission=mission, freelance=request.user
    ).first()
    if existing_candidature:
        messages.warning(request, "Vous avez déjà postulé à cette mission.")
        return redirect("missions:detail", pk=mission.pk)

    if request.method == "POST":
        form = CandidatureForm(request.POST)
        if form.is_valid():
            candidature = form.save(commit=False)
            candidature.mission = mission
            candidature.freelance = request.user
            candidature.save()
            messages.success(request, "Votre candidature a été envoyée avec succès !")
            return redirect("missions:detail", pk=mission.pk)
        else:
            messages.error(request, "Erreur dans le formulaire de candidature.")
    else:
        form = CandidatureForm()

    context = {
        "form": form,
        "mission": mission,
    }
    return render(request, "missions/apply_form.html", context)


@login_required
def my_applications_view(request):
    """Affiche les candidatures envoyées par le freelance connecté."""
    candidatures = Candidature.objects.filter(freelance=request.user).order_by(
        "-date_candidature"
    )
    context = {"candidatures": candidatures}
    return render(request, "missions/my_applications.html", context)


@login_required
def view_candidatures_view(request, mission_pk):
    """Affiche les candidatures reçues pour une mission spécifique (pour le client)."""
    mission = get_object_or_404(Mission, pk=mission_pk)

    if mission.client != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à accéder à cette page.")

    candidatures = mission.candidatures.all().order_by("-date_candidature")

    context = {
        "mission": mission,
        "candidatures": candidatures,
    }
    return render(request, "missions/candidature_list.html", context)


@login_required
@require_POST
def accept_candidature_view(request, candidature_pk):
    """Action pour accepter une candidature (par le client)."""
    candidature = get_object_or_404(Candidature, pk=candidature_pk)
    mission = candidature.mission

    if mission.client != request.user:
        return HttpResponseForbidden("Action non autorisée.")

    if (
        mission.statut == MissionStatus.OPEN
        and candidature.statut == CandidatureStatus.SUBMITTED
    ):
        candidature.statut = CandidatureStatus.ACCEPTED
        candidature.save()

        mission.freelance_assigne = candidature.freelance
        mission.statut = MissionStatus.ASSIGNED
        mission.save()

        autres_candidatures = mission.candidatures.filter(
            statut=CandidatureStatus.SUBMITTED
        )
        autres_candidatures.update(statut=CandidatureStatus.REJECTED)

        messages.success(
            request,
            f"Candidature de {candidature.freelance.username} acceptée ! La mission est maintenant assignée.",
        )
    else:
        messages.error(
            request, "Impossible d'accepter cette candidature (statut invalide)."
        )

    return redirect("missions:view_candidatures", mission_pk=mission.pk)


@login_required
@require_POST
def reject_candidature_view(request, candidature_pk):
    """Action pour refuser une candidature (par le client)."""
    candidature = get_object_or_404(Candidature, pk=candidature_pk)
    mission = candidature.mission

    if mission.client != request.user:
        return HttpResponseForbidden("Action non autorisée.")

    if candidature.statut == CandidatureStatus.SUBMITTED:
        candidature.statut = CandidatureStatus.REJECTED
        candidature.save()
        messages.info(
            request, f"Candidature de {candidature.freelance.username} refusée."
        )
    else:
        messages.warning(request, "Cette candidature n'est plus en attente.")

    return redirect("missions:view_candidatures", mission_pk=mission.pk)


@login_required
def start_conversation_view(request, user_pk):
    """Trouve ou crée une conversation 1-1 avec un autre utilisateur."""
    from messaging.models import Conversation  # Import here to avoid circular import

    target_user = get_object_or_404(User, pk=user_pk)
    current_user = request.user

    if target_user == current_user:
        messages.warning(
            request, "Vous ne pouvez pas démarrer une conversation avec vous-même."
        )
        return redirect("messaging:list")

    conversation = (
        Conversation.objects.annotate(num_participants=Count("participants"))
        .filter(participants=current_user)
        .filter(participants=target_user)
        .filter(num_participants=2)
        .first()
    )

    if conversation is None:
        conversation = Conversation.objects.create()
        conversation.participants.add(current_user, target_user)
        messages.success(
            request, f"Nouvelle conversation démarrée avec {target_user.username}."
        )

    return redirect("messaging:detail", pk=conversation.pk)


@login_required
def leave_evaluation_view(request, mission_pk):
    mission = get_object_or_404(Mission, pk=mission_pk)
    user = request.user

    evaluateur = user
    evalue = None

    if user == mission.client and mission.freelance_assigne:
        evalue = mission.freelance_assigne
    elif user == mission.freelance_assigne:
        evalue = mission.client
    else:
        messages.error(
            request,
            "Vous ne pouvez pas évaluer cette mission dans son état actuel ou vous n'êtes pas concerné.",
        )
        return redirect("missions:detail", pk=mission.pk)

    existing_evaluation = Evaluation.objects.filter(
        mission=mission, evaluateur=evaluateur
    ).first()
    if existing_evaluation:
        messages.warning(
            request, f"Vous avez déjà évalué {evalue.username} pour cette mission."
        )
        return redirect("missions:detail", pk=mission.pk)

    if request.method == "POST":
        form = EvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.mission = mission
            evaluation.evaluateur = evaluateur
            evaluation.evalue = evalue
            evaluation.save()
            messages.success(
                request,
                f"Merci ! Votre évaluation pour {evalue.username} a été enregistrée.",
            )
            return redirect("missions:detail", pk=mission.pk)
        else:
            messages.error(
                request, "Erreur dans le formulaire d'évaluation. Veuillez corriger."
            )
    else:
        form = EvaluationForm()

    context = {
        "form": form,
        "mission": mission,
        "person_to_evaluate": evalue,
    }
    return render(request, "missions/evaluation_form.html", context)


# Ajoutez ces vues à missions/views.py


@login_required
def mission_tracking_dashboard(request):
    """Tableau de bord de suivi des missions"""
    user = request.user
    form = MissionTrackingFilterForm(request.GET or None)

    # Missions où l'utilisateur est impliqué (client ou freelance)
    missions_queryset = (
        Mission.objects.filter(Q(client=user) | Q(freelance_assigne=user))
        .select_related("client", "freelance_assigne")
        .prefetch_related("progress", "milestones", "status_updates")
    )

    # Appliquer les filtres
    if form.is_valid():
        statut = form.cleaned_data.get("statut")
        date_debut = form.cleaned_data.get("date_debut")
        date_fin = form.cleaned_data.get("date_fin")
        retard_uniquement = form.cleaned_data.get("retard_uniquement")

        if statut:
            missions_queryset = missions_queryset.filter(statut=statut)
        if date_debut:
            missions_queryset = missions_queryset.filter(
                date_publication__gte=date_debut
            )
        if date_fin:
            missions_queryset = missions_queryset.filter(date_publication__lte=date_fin)
        if retard_uniquement:
            # Missions avec des jalons en retard
            today = timezone.now().date()
            missions_queryset = missions_queryset.filter(
                milestones__date_prevue__lt=today, milestones__est_complete=False
            ).distinct()

    missions = missions_queryset.order_by("-date_publication")

    # Ajouter le calcul des jalons complétés pour chaque mission
    # Utiliser un nom d'attribut différent de la propriété
    for mission in missions:
        mission.completed_count = mission.milestones.filter(est_complete=True).count()

    # Statistiques
    stats = {
        "total_missions": missions.count(),
        "missions_en_cours": missions.filter(statut="IN_PROGRESS").count(),
        "missions_completees": missions.filter(statut="COMPLETED").count(),
        "missions_en_retard": missions.filter(
            milestones__date_prevue__lt=timezone.now().date(),
            milestones__est_complete=False,
        )
        .distinct()
        .count(),
    }

    # Calcul de l'avancement moyen
    avg_progress = (
        missions.filter(progress__isnull=False).aggregate(
            avg=Avg("progress__pourcentage_completion")
        )["avg"]
        or 0
    )

    context = {
        "missions": missions,
        "filter_form": form,
        "stats": stats,
        "avg_progress": round(avg_progress, 1),
    }
    return render(request, "missions/tracking_dashboard.html", context)


@login_required
def mission_tracking_detail(request, pk):
    """Page détaillée de suivi d'une mission"""
    mission = get_object_or_404(Mission, pk=pk)

    # Vérifier les permissions
    if not (
        mission.client == request.user or mission.freelance_assigne == request.user
    ):
        messages.error(request, "Vous n'avez pas accès au suivi de cette mission.")
        return redirect("missions:list")

    # Obtenir ou créer le suivi de progression
    progress, created = MissionProgress.objects.get_or_create(
        mission=mission,
        defaults={"pourcentage_completion": 0, "mise_a_jour_par": request.user},
    )

    # Récupérer les données de suivi
    milestones = mission.milestones.all().order_by("ordre", "date_prevue")
    comments = (
        mission.comments.filter(Q(auteur=request.user) | Q(est_prive=False))
        .select_related("auteur")
        .order_by("-date_creation")
    )
    status_updates = mission.status_updates.all().select_related("auteur")[:10]

    # Déterminer le rôle de l'utilisateur
    user_role = "client" if mission.client == request.user else "freelance"

    context = {
        "mission": mission,
        "progress": progress,
        "milestones": milestones,
        "comments": comments,
        "status_updates": status_updates,
        "user_role": user_role,
        "can_edit_progress": user_role == "freelance" or mission.client == request.user,
        "can_change_status": True,  # Les deux parties peuvent proposer des changements
    }
    return render(request, "missions/tracking_detail.html", context)


@login_required
def update_mission_progress(request, pk):
    """Mettre à jour le pourcentage d'avancement"""
    mission = get_object_or_404(Mission, pk=pk)

    # Vérifier les permissions (généralement le freelance)
    if not (
        mission.freelance_assigne == request.user or mission.client == request.user
    ):
        messages.error(request, "Vous n'êtes pas autorisé à modifier cette mission.")
        return redirect("missions:detail", pk=pk)

    progress, created = MissionProgress.objects.get_or_create(
        mission=mission, defaults={"mise_a_jour_par": request.user}
    )

    if request.method == "POST":
        form = MissionProgressForm(request.POST, instance=progress)
        if form.is_valid():
            progress = form.save(commit=False)
            progress.mise_a_jour_par = request.user
            progress.save()
            messages.success(request, "Progression mise à jour avec succès!")
            return redirect("missions:tracking_detail", pk=mission.pk)
    else:
        form = MissionProgressForm(instance=progress)

    context = {
        "form": form,
        "mission": mission,
        "progress": progress,
    }
    return render(request, "missions/update_progress.html", context)


@login_required
def update_mission_status(request, pk):
    """Changer le statut d'une mission"""
    mission = get_object_or_404(Mission, pk=pk)

    # Vérifier les permissions
    if not (
        mission.client == request.user or mission.freelance_assigne == request.user
    ):
        messages.error(request, "Vous n'êtes pas autorisé à modifier cette mission.")
        return redirect("missions:detail", pk=pk)

    user_role = "client" if mission.client == request.user else "freelance"

    if request.method == "POST":
        form = MissionStatusUpdateForm(
            request.POST, current_status=mission.statut, user_role=user_role
        )
        if form.is_valid():
            status_update = form.save(commit=False)
            status_update.mission = mission
            status_update.ancien_statut = mission.statut
            status_update.auteur = request.user

            # Mettre à jour le statut de la mission
            mission.statut = status_update.nouveau_statut
            mission.save()
            status_update.save()

            messages.success(
                request,
                f"Statut changé de '{mission.get_statut_display()}' vers '{status_update.get_nouveau_statut_display()}'",
            )
            return redirect("missions:tracking_detail", pk=mission.pk)
    else:
        form = MissionStatusUpdateForm(
            current_status=mission.statut, user_role=user_role
        )

    context = {
        "form": form,
        "mission": mission,
        "user_role": user_role,
    }
    return render(request, "missions/update_status.html", context)


@login_required
def add_milestone(request, pk):
    """Ajouter un jalon à une mission"""
    mission = get_object_or_404(Mission, pk=pk)

    # Seuls le client et le freelance assigné peuvent ajouter des jalons
    if not (
        mission.client == request.user or mission.freelance_assigne == request.user
    ):
        messages.error(request, "Vous n'êtes pas autorisé à ajouter des jalons.")
        return redirect("missions:tracking_detail", pk=pk)

    if request.method == "POST":
        form = MissionMilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.mission = mission
            milestone.created_by = request.user
            milestone.save()
            messages.success(request, "Jalon ajouté avec succès!")
            return redirect("missions:tracking_detail", pk=mission.pk)
    else:
        # Définir l'ordre par défaut
        next_order = mission.milestones.count() + 1
        form = MissionMilestoneForm(initial={"ordre": next_order})

    context = {
        "form": form,
        "mission": mission,
    }
    return render(request, "missions/add_milestone.html", context)


@login_required
def toggle_milestone(request, pk, milestone_id):
    """Basculer l'état d'un jalon (complété/non complété)"""
    mission = get_object_or_404(Mission, pk=pk)
    milestone = get_object_or_404(MissionMilestone, id=milestone_id, mission=mission)

    if not (
        mission.client == request.user or mission.freelance_assigne == request.user
    ):
        return JsonResponse({"error": "Permission refusée"}, status=403)

    if request.method == "POST":
        data = json.loads(request.body)
        milestone.est_complete = data.get("est_complete", False)
        if milestone.est_complete:
            milestone.date_completion = timezone.now().date()
        else:
            milestone.date_completion = None
        milestone.save()

        return JsonResponse(
            {
                "success": True,
                "est_complete": milestone.est_complete,
                "date_completion": (
                    milestone.date_completion.isoformat()
                    if milestone.date_completion
                    else None
                ),
            }
        )

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


@login_required
def add_comment(request, pk):
    """Ajouter un commentaire à une mission"""
    mission = get_object_or_404(Mission, pk=pk)

    if not (
        mission.client == request.user or mission.freelance_assigne == request.user
    ):
        messages.error(request, "Vous n'êtes pas autorisé à commenter cette mission.")
        return redirect("missions:detail", pk=pk)

    if request.method == "POST":
        form = MissionCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.mission = mission
            comment.auteur = request.user
            comment.save()
            messages.success(request, "Commentaire ajouté!")
            return redirect("missions:tracking_detail", pk=mission.pk)
    else:
        form = MissionCommentForm()

    # Si c'est une requête AJAX, retourner JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        if request.method == "POST" and form.is_valid():
            return JsonResponse(
                {
                    "success": True,
                    "comment_html": render_to_string(
                        "missions/comment_item.html",
                        {"comment": comment, "user": request.user},
                    ),
                }
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    context = {
        "form": form,
        "mission": mission,
    }
    return render(request, "missions/add_comment.html", context)
