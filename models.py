from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    subscription_tier = db.Column(db.String(20), default='free')
    stripe_customer_id = db.Column(db.String(50), unique=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), nullable=False)
    current_period_end = db.Column(db.DateTime)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # Duration in seconds

    def calculate_duration(self):
        if self.end_time:
            self.duration = (self.end_time - self.start_time).total_seconds()

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='SaaS Business')
    site_description = db.Column(db.Text, default='Empowering businesses with cutting-edge SaaS solutions.')
    enable_email_verification = db.Column(db.Boolean, default=True)
    allow_social_signup = db.Column(db.Boolean, default=False)
    free_trial_duration = db.Column(db.Integer, default=14)  # in days

class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    features = db.Column(db.Text)  # Store as JSON string

    def get_features(self):
        return json.loads(self.features)

    def set_features(self, features_list):
        self.features = json.dumps(features_list)
