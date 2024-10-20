from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from forms import LoginForm, RegistrationForm
from models import User, Subscription, SubscriptionPlan
from utils import create_stripe_customer, create_stripe_subscription
import stripe
from analytics import get_advanced_analytics

stripe.api_key = app.config['STRIPE_SECRET_KEY']

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        subscription_plan = request.form.get('subscription_plan')
        if subscription_plan not in ['free', 'basic', 'premium']:
            flash('Invalid subscription plan selected.', 'error')
            return redirect(url_for('register'))

        try:
            db.session.begin_nested()

            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            user.subscription_tier = subscription_plan
            db.session.add(user)
            db.session.flush()

            if subscription_plan == 'free':
                db.session.commit()
                login_user(user)
                flash('Registration complete! Welcome to our service.', 'success')
                return redirect(url_for('dashboard'))

            subscription_plan_obj = SubscriptionPlan.query.filter_by(name=subscription_plan).first()
            if not subscription_plan_obj:
                db.session.rollback()
                flash('The selected subscription plan is currently unavailable. Please choose a different plan.', 'error')
                return redirect(url_for('register'))

            customer = create_stripe_customer(user)
            user.stripe_customer_id = customer.id

            checkout_session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': subscription_plan_obj.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=url_for('register_complete', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('register', _external=True),
            )

            db.session.commit()
            return redirect(checkout_session.url, code=303)

        except stripe.error.StripeError as e:
            db.session.rollback()
            app.logger.error(f'Stripe error during registration: {str(e)}')
            flash('We encountered an issue while processing your registration. Please try again or contact support.', 'error')
            return redirect(url_for('register'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Unexpected error during registration: {str(e)}')
            flash('An unexpected error occurred. Please try again or contact support.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html', form=form, stripe_public_key=app.config['STRIPE_PUBLIC_KEY'])

@app.route('/register/complete')
def register_complete():
    session_id = request.args.get('session_id')
    if session_id:
        try:
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            customer = stripe.Customer.retrieve(checkout_session.customer)
            user = User.query.filter_by(stripe_customer_id=customer.id).first()
            if user:
                subscription = create_stripe_subscription(user, checkout_session.subscription)
                db.session.add(subscription)
                db.session.commit()
                login_user(user)
                flash('Registration complete! Welcome to our service.', 'success')
                return redirect(url_for('dashboard'))
            else:
                app.logger.error(f'User not found for Stripe customer ID: {customer.id}')
                flash('We encountered an issue with your registration. Please contact support.', 'error')
        except stripe.error.StripeError as e:
            app.logger.error(f'Stripe error during registration completion: {str(e)}')
            flash('We encountered an issue while completing your registration. Please contact support.', 'error')
    else:
        flash('Invalid registration session. Please try registering again.', 'error')
    return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/pricing')
def pricing():
    plans = SubscriptionPlan.query.all()
    return render_template('pricing.html', plans=plans, stripe_public_key=app.config['STRIPE_PUBLIC_KEY'])

@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/analytics')
@login_required
def analytics():
    analytics_data = get_advanced_analytics()
    return render_template('analytics.html', analytics=analytics_data)