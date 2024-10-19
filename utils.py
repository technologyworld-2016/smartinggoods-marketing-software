import stripe
from app import app
from models import Subscription
from functools import wraps
from flask import abort
from flask_login import current_user

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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
