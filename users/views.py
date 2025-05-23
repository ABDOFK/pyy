# users/views.py
# ... (imports existants)
from .forms import FreelanceProfileForm, ClientProfileForm # Ajoutez ceux-là
from .models import FreelanceProfile, ClientProfile # Et ceux-là
from django.shortcuts import get_object_or_404 # Utile, mais pas strictement nécessaire avec notre approche
# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages # Pour afficher des messages flash
from django.contrib.auth.decorators import login_required # Pour protéger certaines vues

# Importez vos formulaires personnalisés (si vous les utilisez)
# from .forms import CustomUserCreationForm, CustomAuthenticationForm
# Ou les formulaires par défaut/personnalisés :
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from missions.models import Evaluation


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Crée et sauvegarde le nouvel utilisateur
            # login(request, user) # Connecte l'utilisateur automatiquement après inscription (optionnel)
            messages.success(request, "Inscription réussie ! Vous pouvez maintenant vous connecter.")
            return redirect('users:login') # Redirige vers la page de connexion
        else:
            # Si le formulaire n'est pas valide, les erreurs seront dans form.errors
            messages.error(request, "Erreur lors de l'inscription. Veuillez corriger les erreurs ci-dessous.")
    else: # Si c'est une requête GET (accès initial à la page)
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home') # Ou une page de tableau de bord, si l'utilisateur est déjà connecté

    if request.method == 'POST':
        # Utilisez AuthenticationForm directement ou votre CustomAuthenticationForm
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Bienvenue {username}.")
                # Rediriger vers une page 'next' si elle existe (souvent utilisé par @login_required)
                next_url = request.POST.get('next', '/') # Redirige vers la page d'accueil par défaut
                # Ou rediriger vers un tableau de bord spécifique : return redirect('dashboard')
                return redirect(next_url or 'home') # 'home' est un nom d'URL qu'on définira plus tard
            else:
                messages.error(request,"Nom d'utilisateur ou mot de passe incorrect.")
        else:
            messages.error(request,"Nom d'utilisateur ou mot de passe incorrect.")
    else: # Requête GET
        form = AuthenticationForm()
        # Récupérer le paramètre 'next' s'il existe (pour la redirection après login)
        next_url = request.GET.get('next', '')
    return render(request, 'users/login.html', {'form': form, 'next': next_url})



# La vue de déconnexion est simple
def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('home') # Redirige vers la page d'accueil
# users/views.py
# ... (vues register, login, logout)

@login_required
def update_freelance_profile(request):
    # Essayer de récupérer le profil existant, ou None s'il n'existe pas
    try:
        profile_instance = request.user.freelance_profile
    except FreelanceProfile.DoesNotExist:
        profile_instance = None

    if request.method == 'POST':
        # Passer 'instance=profile_instance' pour pré-remplir si modification,
        # ou pour lier correctement lors de la création si profile_instance est None.
        form = FreelanceProfileForm(request.POST, request.FILES or None, instance=profile_instance) # request.FILES pour les uploads (ex: photo)
        if form.is_valid():
            profile = form.save(commit=False) # Ne sauvegarde pas encore en BDD
            profile.user = request.user      # Lie le profil à l'utilisateur connecté
            profile.save()                   # Sauvegarde en BDD
            messages.success(request, "Profil Freelance mis à jour avec succès !")
            return redirect('users:profile') # Redirige vers la page de profil principale
        else:
            messages.error(request, "Erreur lors de la mise à jour du profil.")
    else: # Requête GET
        form = FreelanceProfileForm(instance=profile_instance)

    context = {
        'form': form,
        'profile_type': 'Freelance'
    }
    return render(request, 'users/profile_form.html', context)

@login_required
def update_client_profile(request):
    # Logique similaire pour le profil Client
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
    else: # Requête GET
        form = ClientProfileForm(instance=profile_instance)

    context = {
        'form': form,
        'profile_type': 'Client'
    }
    return render(request, 'users/profile_form.html', context)

# Modifions la vue de profil principale pour afficher les infos et les liens
@login_required
def profile_view(request):
    # Récupérer les profils (ils seront None s'ils n'existent pas)
    freelance_profile = getattr(request.user, 'freelance_profile', None)
    client_profile = getattr(request.user, 'client_profile', None)

    context = {
        'user': request.user,
        'freelance_profile': freelance_profile,
        'client_profile': client_profile,
    }
    return render(request, 'users/profile.html', context) # On utilise le template profile.html existant
# Exemple de vue protégée (nécessite d'être connecté)
@login_required # Ce décorateur redirige vers la page de login si l'utilisateur n'est pas connecté
def profile_view(request):
    # Ici, vous récupéreriez le profil Freelance ou Client de request.user
    # freelance_profile = getattr(request.user, 'freelance_profile', None)
    # client_profile = getattr(request.user, 'client_profile', None)
    # context = {'freelance_profile': freelance_profile, 'client_profile': client_profile}
    # Pour l'instant, juste un exemple simple
    return render(request, 'users/profile.html') # Créez ce template plus tard

@login_required

def profile_view(request):
    # --- PROBLÈME PROBABLE ICI ---
    # Vous devez DÉFINIR ces variables AVANT de les utiliser dans le 'context'
    freelance_profile = getattr(request.user, 'freelance_profile', None) # Définition
    client_profile = getattr(request.user, 'client_profile', None)      # Définition
    # --- FIN PROBLÈME PROBABLE ---
    
    evaluations_recues = Evaluation.objects.filter(evalue=request.user).order_by('-date_evaluation')

    context = {
        'user': request.user,
        'freelance_profile': freelance_profile, # Utilisation
        'client_profile': client_profile,      # Utilisation
        'evaluations_recues': evaluations_recues,
    }
    return render(request, 'users/profile.html', context)