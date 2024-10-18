import stripe
from app import app
from models import Subscription

stripe.api_key = app.config['STRIPE_SECRET_KEY']

def create_stripe_customer(user):
    customer = stripe.Customer.create(
        email=user.email,
        name=user.username
    )
    return customer

def create_stripe_subscription(user, subscription_id):
    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
    subscription = Subscription(
        user_id=user.id,
        stripe_subscription_id=subscription_id,
        status=stripe_subscription.status,
        current_period_end=stripe_subscription.current_period_end
    )
    return subscription
