import stripe
import requests
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Configuration Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_...')

class StripePaymentService:
    """Service de paiement Stripe"""
    
    @staticmethod
    def create_payment_intent(facture, success_url: str, cancel_url: str) -> Dict:
        """Crée un Payment Intent Stripe"""
        try:
            # Convertir en centimes pour Stripe
            amount_cents = int(facture.montant_ttc * 100)
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='eur',
                metadata={
                    'facture_id': str(facture.id),
                    'facture_reference': facture.reference_facture,
                    'client_id': str(facture.client.id),
                    'freelance_id': str(facture.freelance.id),
                },
                description=f"Paiement pour {facture.reference_facture}",
                receipt_email=facture.client.email,
                automatic_payment_methods={'enabled': True},
            )
            
            # Sauvegarder l'ID du Payment Intent
            facture.stripe_payment_intent_id = payment_intent.id
            facture.save()
            
            return {
                'success': True,
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'publishable_key': getattr(settings, 'STRIPE_PUBLISHABLE_KEY', 'pk_test_...'),
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def confirm_payment(payment_intent_id: str) -> Tuple[bool, str]:
        """Confirme un paiement Stripe"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status == 'succeeded':
                return True, "Paiement confirmé avec succès"
            else:
                return False, f"Statut de paiement: {payment_intent.status}"
                
        except stripe.error.StripeError as e:
            logger.error(f"Erreur confirmation Stripe: {e}")
            return False, str(e)
    
    @staticmethod
    def create_checkout_session(facture, success_url: str, cancel_url: str) -> Dict:
        """Crée une session Stripe Checkout"""
        try:
            # Convertir en centimes pour Stripe
            amount_cents = int(facture.montant_ttc * 100)
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f'Facture {facture.reference_facture}',
                            'description': f'Paiement pour la mission: {facture.mission.titre if facture.mission else "Service FreelanceHub"}',
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                metadata={
                    'facture_id': str(facture.id),
                    'facture_reference': facture.reference_facture,
                },
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=facture.client.email,
            )
            
            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe Checkout: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class PayPalPaymentService:
    """Service de paiement PayPal"""
    
    def __init__(self):
        self.client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', '')
        self.base_url = getattr(settings, 'PAYPAL_BASE_URL', 'https://api.sandbox.paypal.com')  # sandbox par défaut
    
    def get_access_token(self) -> Optional[str]:
        """Obtient un token d'accès PayPal"""
        try:
            url = f"{self.base_url}/v1/oauth2/token"
            
            headers = {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
            }
            
            data = 'grant_type=client_credentials'
            
            response = requests.post(
                url,
                headers=headers,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"Erreur token PayPal: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur PayPal token: {e}")
            return None
    
    def create_order(self, facture, success_url: str, cancel_url: str) -> Dict:
        """Crée une commande PayPal"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Impossible d\'obtenir le token PayPal'}
            
            url = f"{self.base_url}/v2/checkout/orders"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            
            order_data = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {
                        'currency_code': 'EUR',
                        'value': str(facture.montant_ttc)
                    },
                    'description': f'Facture {facture.reference_facture}',
                    'reference_id': facture.reference_facture,
                }],
                'application_context': {
                    'return_url': success_url,
                    'cancel_url': cancel_url,
                    'brand_name': 'FreelanceHub',
                    'user_action': 'PAY_NOW'
                }
            }
            
            response = requests.post(url, headers=headers, json=order_data)
            
            if response.status_code == 201:
                order = response.json()
                
                # Sauvegarder l'ID de la commande
                facture.paypal_order_id = order['id']
                facture.save()
                
                # Trouver l'URL d'approbation
                approval_url = None
                for link in order.get('links', []):
                    if link.get('rel') == 'approve':
                        approval_url = link.get('href')
                        break
                
                return {
                    'success': True,
                    'order_id': order['id'],
                    'approval_url': approval_url
                }
            else:
                logger.error(f"Erreur création commande PayPal: {response.text}")
                return {'success': False, 'error': 'Erreur lors de la création de la commande PayPal'}
                
        except Exception as e:
            logger.error(f"Erreur PayPal: {e}")
            return {'success': False, 'error': str(e)}
    
    def capture_order(self, order_id: str) -> Tuple[bool, str, Optional[str]]:
        """Capture une commande PayPal"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False, 'Impossible d\'obtenir le token PayPal', None
            
            url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            
            response = requests.post(url, headers=headers)
            
            if response.status_code == 201:
                capture_data = response.json()
                capture_id = capture_data.get('purchase_units', [{}])[0].get('payments', {}).get('captures', [{}])[0].get('id')
                return True, 'Paiement capturé avec succès', capture_id
            else:
                logger.error(f"Erreur capture PayPal: {response.text}")
                return False, f'Erreur lors de la capture: {response.text}', None
                
        except Exception as e:
            logger.error(f"Erreur capture PayPal: {e}")
            return False, str(e), None

class EscrowService:
    """Service de gestion du séquestre"""
    
    @staticmethod
    def create_escrow_account(facture) -> bool:
        """Crée un compte de séquestre pour une facture"""
        try:
            from .models import EscrowAccount
            
            escrow_account = EscrowAccount.objects.create(
                facture=facture,
                montant_bloque=facture.montant_ttc
            )
            
            logger.info(f"Compte séquestre créé pour la facture {facture.reference_facture}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur création séquestre: {e}")
            return False
    
    @staticmethod
    def release_funds(facture) -> bool:
        """Libère les fonds du séquestre"""
        try:
            from django.utils import timezone
            
            escrow_account = facture.escrow_account
            escrow_account.est_libere = True
            escrow_account.date_liberation = timezone.now()
            escrow_account.save()
            
            # Ici vous pourriez déclencher le virement vers le freelance
            logger.info(f"Fonds libérés pour la facture {facture.reference_facture}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur libération fonds: {e}")
            return False

class PaymentProcessor:
    """Processeur principal de paiements"""
    
    def __init__(self):
        self.stripe_service = StripePaymentService()
        self.paypal_service = PayPalPaymentService()
        self.escrow_service = EscrowService()
    
    def initiate_payment(self, facture, method: str, success_url: str, cancel_url: str) -> Dict:
        """Initie un paiement selon la méthode choisie"""
        if method == 'STRIPE':
            return self.stripe_service.create_checkout_session(facture, success_url, cancel_url)
        elif method == 'PAYPAL':
            return self.paypal_service.create_order(facture, success_url, cancel_url)
        elif method == 'ESCROW':
            # Pour le séquestre, on redirige vers une page de confirmation
            return {
                'success': True,
                'redirect_url': reverse('payments:escrow_payment', kwargs={'facture_uuid': facture.uuid})
            }
        else:
            return {'success': False, 'error': 'Méthode de paiement non supportée'}
    
    def process_webhook(self, provider: str, payload: Dict) -> bool:
        """Traite les webhooks des fournisseurs de paiement"""
        try:
            from .models import PaymentWebhook
            
            # Enregistrer le webhook
            webhook = PaymentWebhook.objects.create(
                provider=provider,
                event_type=payload.get('type', 'unknown'),
                webhook_id=payload.get('id', ''),
                payload=payload
            )
            
            if provider == 'stripe':
                return self._process_stripe_webhook(payload)
            elif provider == 'paypal':
                return self._process_paypal_webhook(payload)
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur traitement webhook {provider}: {e}")
            return False
    
    def _process_stripe_webhook(self, payload: Dict) -> bool:
        """Traite les webhooks Stripe"""
        try:
            from .models import Facture, Paiement, PaiementStatus
            
            event_type = payload.get('type')
            
            if event_type == 'payment_intent.succeeded':
                payment_intent = payload['data']['object']
                payment_intent_id = payment_intent['id']
                
                # Trouver la facture
                facture = Facture.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
                if facture:
                    # Créer le paiement
                    paiement = Paiement.objects.create(
                        facture=facture,
                        montant=Decimal(payment_intent['amount']) / 100,  # Convertir les centimes
                        methode_paiement='STRIPE',
                        statut=PaiementStatus.SUCCESS,
                        stripe_payment_intent_id=payment_intent_id,
                        reference_transaction=payment_intent_id,
                        details_passerelle=payload
                    )
                    
                    # Confirmer le paiement
                    paiement.confirm_payment()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur webhook Stripe: {e}")
            return False
    
    def _process_paypal_webhook(self, payload: Dict) -> bool:
        """Traite les webhooks PayPal"""
        try:
            from .models import Facture, Paiement, PaiementStatus
            
            event_type = payload.get('event_type')
            
            if event_type == 'CHECKOUT.ORDER.APPROVED':
                resource = payload.get('resource', {})
                order_id = resource.get('id')
                
                # Trouver la facture
                facture = Facture.objects.filter(paypal_order_id=order_id).first()
                if facture:
                    # Capturer automatiquement la commande
                    success, message, capture_id = self.paypal_service.capture_order(order_id)
                    
                    if success:
                        # Créer le paiement
                        paiement = Paiement.objects.create(
                            facture=facture,
                            montant=facture.montant_ttc,
                            methode_paiement='PAYPAL',
                            statut=PaiementStatus.SUCCESS,
                            paypal_capture_id=capture_id,
                            reference_transaction=capture_id,
                            details_passerelle=payload
                        )
                        
                        # Confirmer le paiement
                        paiement.confirm_payment()
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur webhook PayPal: {e}")
            return False