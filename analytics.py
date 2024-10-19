from datetime import datetime, timedelta
from app import db
from models import User, Subscription, UserSession
from sqlalchemy import func

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
    
    # Calculate subscription growth rate
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_subscriptions = Subscription.query.filter(Subscription.created_at >= thirty_days_ago).count()
    subscription_growth_rate = (new_subscriptions / total_subscriptions) if total_subscriptions > 0 else 0
    
    # Calculate average subscription duration using PostgreSQL's date functions
    avg_duration = db.session.query(func.avg(func.extract('epoch', Subscription.current_period_end - Subscription.created_at) / 86400)).scalar() or 0
    
    return {
        'total': total_subscriptions,
        'active': active_subscriptions,
        'cancelled': cancelled_subscriptions,
        'churn_rate': cancelled_subscriptions / total_subscriptions if total_subscriptions > 0 else 0,
        'growth_rate': subscription_growth_rate,
        'avg_duration': avg_duration
    }

def get_user_engagement_metrics():
    total_users = User.query.count()
    active_users_30d = get_active_users(30)
    active_users_7d = get_active_users(7)
    
    # Calculate user retention rate
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    retained_users = User.query.filter(User.created_at <= thirty_days_ago, User.last_login >= thirty_days_ago).count()
    retention_rate = retained_users / total_users if total_users > 0 else 0
    
    # Calculate average session duration
    avg_session_duration = db.session.query(func.avg(UserSession.duration)).scalar() or 0
    
    # Calculate conversion rate
    paid_users = User.query.filter(User.subscription_tier != 'free').count()
    conversion_rate = paid_users / total_users if total_users > 0 else 0
    
    # Calculate daily active users (DAU)
    dau = get_active_users(1)
    
    # Calculate monthly active users (MAU)
    mau = active_users_30d
    
    # Calculate DAU/MAU ratio
    dau_mau_ratio = dau / mau if mau > 0 else 0
    
    return {
        'total_users': total_users,
        'active_users_30d': active_users_30d,
        'active_users_7d': active_users_7d,
        'engagement_rate_30d': active_users_30d / total_users if total_users > 0 else 0,
        'engagement_rate_7d': active_users_7d / total_users if total_users > 0 else 0,
        'retention_rate': retention_rate,
        'avg_session_duration': avg_session_duration,
        'conversion_rate': conversion_rate,
        'dau': dau,
        'mau': mau,
        'dau_mau_ratio': dau_mau_ratio
    }

def calculate_arpu():
    total_revenue = db.session.query(func.sum(Subscription.amount)).scalar() or 0
    total_users = User.query.count()
    return total_revenue / total_users if total_users > 0 else 0

def calculate_ltv():
    arpu = calculate_arpu()
    avg_subscription_duration = get_subscription_metrics()['avg_duration']
    return arpu * avg_subscription_duration

def get_advanced_analytics():
    user_metrics = get_user_engagement_metrics()
    subscription_metrics = get_subscription_metrics()
    arpu = calculate_arpu()
    ltv = calculate_ltv()
    
    return {
        'user_metrics': user_metrics,
        'subscription_metrics': subscription_metrics,
        'arpu': arpu,
        'ltv': ltv
    }
