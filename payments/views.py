from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q, Sum
from django.core.paginator import Paginator

from .models import Facture, Paiement, EscrowAccount, FactureStatus, PaymentMethod
from .forms import PaymentMethodForm, QuickInvoiceForm, BankTransferForm, EscrowReleaseForm, PaymentFilterForm
from missions.models import Mission

@login_required
def payment_dashboard(request):
    """Tableau de bord des paiements"""
    user = request.user
    
    # Statistiques pour le client
    if user.factures_recues.exists():
        factures_recues = user.factures_recues.all()
        stats_client = {
            'total_factures': factures_recues.count(),
            'factures_payees': factures_recues.filter(statut=FactureStatus.PAID).count(),
            'factures_en_attente': factures_recues.filter(statut=FactureStatus.SENT).count(),
            'factures_en_retard': factures_recues.filter(statut=FactureStatus.OVERDUE).count(),
            'montant_total': factures_recues.aggregate(Sum('montant_ttc'))['montant_ttc__sum'] or 0,
            'montant_paye': factures_recues.filter(statut=FactureStatus.PAID).aggregate(Sum('montant_ttc'))['montant_ttc__sum'] or 0,
        }
    else:
        stats_client = None
    
    # Statistiques pour le freelance
    if user.factures_emises.exists():
        factures_emises = user.factures_emises.all()
        stats_freelance = {
            'total_factures': factures_emises.count(),
            'factures_payees': factures_emises.filter(statut=FactureStatus.PAID).count(),
            'factures_en_attente': factures_emises.filter(statut=FactureStatus.SENT).count(),
            'montant_total': factures_emises.aggregate(Sum('montant_freelance'))['montant_freelance__sum'] or 0,
            'montant_recu': factures_emises.filter(statut=FactureStatus.PAID).aggregate(Sum('montant_freelance'))['montant_freelance__sum'] or 0,
        }
    else:
        stats_freelance = None
    
    # Factures récentes
    recent_factures = Facture.objects.filter(
        Q(client=user) | Q(freelance=user)
    ).order_by('-date_emission')[:5]
    
    # Paiements récents
    recent_payments = Paiement.objects.filter(
        facture__client=user
    ).order_by('-date_paiement')[:5]
    
    context = {
        'stats_client': stats_client,
        'stats_freelance': stats_freelance,
        'recent_factures': recent_factures,
        'recent_payments': recent_payments,
    }
    return render(request, 'payments/dashboard.html', context)

@login_required
def create_invoice_from_mission(request, mission_id):
    """Créer une facture à partir d'une mission"""
    mission = get_object_or_404(Mission, id=mission_id)
    
    # Vérifier les permissions
    if not (mission.freelance_assigne == request.user or mission.client == request.user):
        messages.error(request, "Vous n'êtes pas autorisé à créer une facture pour cette mission.")
        return redirect('missions:detail', pk=mission.id)
    
    # Vérifier qu'une facture n'existe pas déjà
    existing_facture = Facture.objects.filter(mission=mission).first()
    if existing_facture:
        messages.info(request, "Une facture existe déjà pour cette mission.")
        return redirect('payments:invoice_detail', pk=existing_facture.pk)
    
    if request.method == 'POST':
        form = QuickInvoiceForm(request.POST)
        if form.is_valid():
            # Créer la facture
            facture = Facture.objects.create(
                mission=mission,
                client=mission.client,
                freelance=mission.freelance_assigne,
                montant_ht=form.cleaned_data['montant_ht'],
                tva_taux=form.cleaned_data['tva_taux'],
                date_echeance=form.cleaned_data['date_echeance'],
                notes=form.cleaned_data.get('description', ''),
                statut=FactureStatus.SENT
            )
            
            messages.success(request, f"Facture {facture.reference_facture} créée avec succès!")
            return redirect('payments:invoice_detail', pk=facture.pk)
    else:
        form = QuickInvoiceForm()
    
    context = {
        'form': form,
        'mission': mission,
    }
    return render(request, 'payments/create_invoice.html', context)

@login_required
def invoice_detail(request, pk):
    """Détails d'une facture"""
    facture = get_object_or_404(Facture, pk=pk)
    
    # Vérifier les permissions
    if not (facture.client == request.user or facture.freelance == request.user):
        return HttpResponseForbidden("Vous n'êtes pas autorisé à voir cette facture.")
    
    # Paiements associés
    paiements = facture.paiements.all().order_by('-date_paiement')
    
    # Compte séquestre si applicable
    escrow_account = getattr(facture, 'escrow_account', None)
    
    context = {
        'facture': facture,
        'paiements': paiements,
        'escrow_account': escrow_account,
        'can_pay': facture.can_be_paid and facture.client == request.user,
        'can_release_escrow': escrow_account and not escrow_account.est_libere and facture.client == request.user,
    }
    return render(request, 'payments/invoice_detail.html', context)

@login_required
def payment_page(request, pk):
    """Page de paiement d'une facture"""
    facture = get_object_or_404(Facture, pk=pk)
    
    # Vérifier les permissions et l'état
    if facture.client != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à payer cette facture.")
    
    if not facture.can_be_paid:
        messages.error(request, "Cette facture ne peut pas être payée.")
        return redirect('payments:invoice_detail', pk=pk)
    
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data['method']
            
            if method == 'ESCROW':
                return redirect('payments:escrow_payment', pk=pk)
            elif method == 'BANK_TRANSFER':
                return redirect('payments:bank_transfer', pk=pk)
            else:
                messages.error(request, f"Méthode de paiement {method} non disponible pour le moment.")
    else:
        form = PaymentMethodForm()
    
    context = {
        'facture': facture,
        'form': form,
    }
    return render(request, 'payments/payment_page.html', context)

@login_required
def payment_success(request, pk):
    """Page de succès de paiement"""
    facture = get_object_or_404(Facture, pk=pk)
    
    context = {
        'facture': facture,
    }
    return render(request, 'payments/payment_success.html', context)

@login_required
def payment_cancel(request, pk):
    """Page d'annulation de paiement"""
    facture = get_object_or_404(Facture, pk=pk)
    
    context = {
        'facture': facture,
    }
    return render(request, 'payments/payment_cancel.html', context)

@login_required
def bank_transfer_payment(request, pk):
    """Paiement par virement bancaire"""
    facture = get_object_or_404(Facture, pk=pk)
    
    if facture.client != request.user or not facture.can_be_paid:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à effectuer cette action.")
    
    if request.method == 'POST':
        form = BankTransferForm(request.POST)
        if form.is_valid():
            # Créer un paiement en attente
            Paiement.objects.create(
                facture=facture,
                montant=facture.montant_ttc,
                methode_paiement=PaymentMethod.BANK_TRANSFER,
                statut='PROCESSING',
            )
            
            messages.success(request, "Votre déclaration de virement a été enregistrée.")
            return redirect('payments:invoice_detail', pk=pk)
    else:
        form = BankTransferForm()
    
    context = {
        'facture': facture,
        'form': form,
    }
    return render(request, 'payments/bank_transfer.html', context)

@login_required
def escrow_payment(request, pk):
    """Paiement via séquestre"""
    facture = get_object_or_404(Facture, pk=pk)
    
    if facture.client != request.user or not facture.can_be_paid:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à effectuer cette action.")
    
    if request.method == 'POST':
        # Créer le compte séquestre
        escrow_account = EscrowAccount.objects.create(
            facture=facture,
            montant_bloque=facture.montant_ttc
        )
        
        # Marquer la facture comme payée (fonds en séquestre)
        facture.statut = FactureStatus.PAID
        facture.save()
        
        # Créer un enregistrement de paiement
        Paiement.objects.create(
            facture=facture,
            montant=facture.montant_ttc,
            methode_paiement=PaymentMethod.ESCROW,
            statut='SUCCESS',
        )
        
        messages.success(request, "Les fonds ont été placés en séquestre.")
        return redirect('payments:invoice_detail', pk=pk)
    
    context = {
        'facture': facture,
    }
    return render(request, 'payments/escrow_payment.html', context)

@login_required
def release_escrow(request, pk):
    """Libérer les fonds du séquestre"""
    facture = get_object_or_404(Facture, pk=pk)
    
    if facture.client != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à effectuer cette action.")
    
    try:
        escrow_account = facture.escrow_account
        if escrow_account.est_libere:
            messages.warning(request, "Les fonds ont déjà été libérés.")
            return redirect('payments:invoice_detail', pk=pk)
    except:
        messages.error(request, "Aucun compte séquestre trouvé pour cette facture.")
        return redirect('payments:invoice_detail', pk=pk)
    
    if request.method == 'POST':
        form = EscrowReleaseForm(request.POST)
        if form.is_valid():
            from django.utils import timezone
            
            escrow_account.est_libere = True
            escrow_account.date_liberation = timezone.now()
            escrow_account.save()
            
            messages.success(request, f"Les fonds ont été libérés vers {facture.freelance.username}.")
            return redirect('payments:invoice_detail', pk=pk)
    else:
        form = EscrowReleaseForm()
    
    context = {
        'facture': facture,
        'escrow_account': escrow_account,
        'form': form,
    }
    return render(request, 'payments/release_escrow.html', context)

@login_required
def invoice_list(request):
    """Liste des factures de l'utilisateur"""
    user = request.user
    
    # Déterminer le rôle
    role = request.GET.get('role', 'client')
    
    if role == 'freelance':
        factures = Facture.objects.filter(freelance=user)
        page_title = "Mes Factures Émises"
    else:
        factures = Facture.objects.filter(client=user)
        page_title = "Mes Factures Reçues"
    
    factures = factures.order_by('-date_emission')
    
    # Pagination
    paginator = Paginator(factures, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'role': role,
        'page_title': page_title,
    }
    return render(request, 'payments/invoice_list.html', context)