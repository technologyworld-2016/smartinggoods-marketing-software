from datetime import datetime
from app import db
from models import User, Subscription

def track_user_login(user_id):
    user = User.query.get(user_id)
    if user:
        user.last_login = datetime.utcnow()
        db.session.commit()

def get_active_users(days=30):
    thirty_days_ago = datetime.utcnow() - timedelta(days=days)
    return User.query.filter(User.last_login >= thirty_days_ago).count()

def get_subscription_metrics():
    total_subscriptions = Subscription.query.count()
    active_subscriptions = Subscription.query.filter_by(status='active').count()
    cancelled_subscriptions = Subscription.query.filter_by(status='cancelled').count()
    
    return {
        'total': total_subscriptions,
        'active': active_subscriptions,
        'cancelled': cancelled_subscriptions,
        'churn_rate': cancelled_subscriptions / total_subscriptions if total_subscriptions > 0 else 0
    }

def get_user_engagement_metrics():
    total_users = User.query.count()
    active_users_30d = get_active_users(30)
    active_users_7d = get_active_users(7)
    
    return {
        'total_users': total_users,
        'active_users_30d': active_users_30d,
        'active_users_7d': active_users_7d,
        'engagement_rate_30d': active_users_30d / total_users if total_users > 0 else 0,
        'engagement_rate_7d': active_users_7d / total_users if total_users > 0 else 0
    }
