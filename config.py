import os

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'a-very-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI += "?sslmode=verify-full&sslrootcert=system"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STRIPE_PUBLIC_KEY = 'pk_test_jKTXUbmDj3ovl1kCmGqgF8Zn'
    STRIPE_SECRET_KEY = 'sk_test_JJPywAP5oQprINcl44POEcJU'
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
