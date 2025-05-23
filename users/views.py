# users/views.py - Version complète
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Q

from .forms import CustomUserCreationForm, FreelanceProfileForm, ClientProfileForm, FreelanceSearchForm
from .models import FreelanceProfile, ClientProfile
from missions.models import Evaluation, Mission

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Inscription réussie ! Vous pouvez maintenant vous connecter.")
            return redirect('users:login')
        else:
            messages.error(request, "Erreur lors de l'inscription. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Bienvenue {username}.")
                next_url = request.POST.get('next', '/')
                return redirect(next_url or 'home')
            else:
                messages.error(request,"Nom d'utilisateur ou mot de passe incorrect.")
        else:
            messages.error(request,"Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = AuthenticationForm()
        next_url = request.GET.get('next', '')
    return render(request, 'users/login.html', {'form': form, 'next': next_url})

def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('home')

@login_required
def update_freelance_profile(request):
    try:
        profile_instance = request.user.freelance_profile
    except FreelanceProfile.DoesNotExist:
        profile_instance = None

    if request.method == 'POST':
        form = FreelanceProfileForm(request.POST, request.FILES or None, instance=profile_instance)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profil Freelance mis à jour avec succès !")
            return redirect('users:profile')
        else:
            messages.error(request, "Erreur lors de la mise à jour du profil.")
    else:
        form = FreelanceProfileForm(instance=profile_instance)

    context = {
        'form': form,
        'profile_type': 'Freelance'
    }
    return render(request, 'users/profile_form.html', context)

@login_required
def update_client_profile(request):
    try:
        profile_instance = request.user.client_profile
    except ClientProfile.DoesNotExist:
        profile_instance = None

    if request.method == 'POST':
        form = ClientProfileForm(request.POST, request.FILES or None, instance=profile_instance)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profil Client mis à jour avec succès !")
            return redirect('users:profile')
        else:
            messages.error(request, "Erreur lors de la mise à jour du profil.")
    else:
        form = ClientProfileForm(instance=profile_instance)

    context = {
        'form': form,
        'profile_type': 'Client'
    }
    return render(request, 'users/profile_form.html', context)

@login_required
def profile_view(request):
    freelance_profile = getattr(request.user, 'freelance_profile', None)
    client_profile = getattr(request.user, 'client_profile', None)
    evaluations_recues = Evaluation.objects.filter(evalue=request.user).order_by('-date_evaluation')

    context = {
        'user': request.user,
        'freelance_profile': freelance_profile,
        'client_profile': client_profile,
        'evaluations_recues': evaluations_recues,
    }
    return render(request, 'users/profile.html', context)

@login_required
def freelance_search_view(request):
    """Permet aux clients de rechercher des freelances."""
    queryset = FreelanceProfile.objects.filter(
        titre_professionnel__isnull=False
    ).exclude(
        titre_professionnel__exact=''
    ).select_related('user').order_by('-id')
    
    form = FreelanceSearchForm(request.GET or None)
    
    if form.is_valid():
        keywords = form.cleaned_data.get('keywords')
        competences = form.cleaned_data.get('competences')
        taux_min = form.cleaned_data.get('taux_min')
        taux_max = form.cleaned_data.get('taux_max')
        disponibilite = form.cleaned_data.get('disponibilite')
        
        if keywords:
            queryset = queryset.filter(
                Q(titre_professionnel__icontains=keywords) | 
                Q(experience__icontains=keywords) |
                Q(user__first_name__icontains=keywords) |
                Q(user__last_name__icontains=keywords)
            )
        
        if competences:
            competences_list = [comp.strip() for comp in competences.split(',') if comp.strip()]
            for comp_item in competences_list:
                queryset = queryset.filter(competences__icontains=comp_item)
        
        if taux_min:
            queryset = queryset.filter(taux_journalier__gte=taux_min)
        if taux_max:
            queryset = queryset.filter(taux_journalier__lte=taux_max)
        
        if disponibilite:
            queryset = queryset.filter(disponibilite__icontains=disponibilite)
    
    context = {
        'freelances': queryset,
        'search_form': form,
        'total_count': queryset.count(),
    }
    return render(request, 'users/freelance_search.html', context)

@login_required  
def freelance_profile_view(request, user_id):
    """Affiche le profil public d'un freelance."""
    freelance_user = get_object_or_404(User, id=user_id)
    
    try:
        freelance_profile = freelance_user.freelance_profile
    except FreelanceProfile.DoesNotExist:
        messages.error(request, "Ce freelance n'a pas de profil public.")
        return redirect('users:freelance_search')
    
    evaluations_recues = Evaluation.objects.filter(
        evalue=freelance_user
    ).select_related('evaluateur', 'mission').order_by('-date_evaluation')[:5]
    
    if evaluations_recues:
        note_moyenne = sum(eval.note for eval in evaluations_recues) / len(evaluations_recues)
        note_moyenne = round(note_moyenne, 1)
    else:
        note_moyenne = None
    
    missions_terminees = Mission.objects.filter(
        freelance_assigne=freelance_user,
        statut__in=['COMPLETED', 'CLOSED']
    ).order_by('-date_publication')[:3]
    
    context = {
        'freelance_user': freelance_user,
        'freelance_profile': freelance_profile,
        'evaluations_recues': evaluations_recues,
        'note_moyenne': note_moyenne,
        'missions_terminees': missions_terminees,
        'total_evaluations': len(evaluations_recues),
    }
    return render(request, 'users/freelance_profile_public.html', context)