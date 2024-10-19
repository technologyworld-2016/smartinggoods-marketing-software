from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db, login_manager
from models import User, Subscription, UserSession
from forms import LoginForm, RegistrationForm
from utils import create_stripe_customer, create_stripe_subscription
from analytics import track_user_login, get_advanced_analytics
import stripe
from datetime import datetime

stripe.api_key = app.config['STRIPE_SECRET_KEY']

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            track_user_login(user.id)
            session = UserSession(user_id=user.id)
            db.session.add(session)
            db.session.commit()
            return redirect(url_for('dashboard'))
        flash('Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    session = UserSession.query.filter_by(user_id=current_user.id, end_time=None).first()
    if session:
        session.end_time = datetime.utcnow()
        session.calculate_duration()
        db.session.commit()
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    recent_activity = UserSession.query.filter_by(user_id=current_user.id).order_by(UserSession.start_time.desc()).limit(5).all()
    
    if current_user.is_admin:
        users = User.query.all()
        subscriptions = Subscription.query.all()
        return render_template('dashboard.html', users=users, subscriptions=subscriptions, user_subscription=user_subscription, recent_activity=recent_activity)
    
    return render_template('dashboard.html', user_subscription=user_subscription, recent_activity=recent_activity)

@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/analytics')
@login_required
def analytics():
    advanced_analytics = get_advanced_analytics()
    return render_template('analytics.html', analytics=advanced_analytics)

@app.route('/dashboard/subscription')
@login_required
def subscription_dashboard():
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    billing_history = []
    return render_template('subscription_dashboard.html', user=current_user, subscription=subscription, billing_history=billing_history)

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        price_id = request.json['priceId']
        
        if not current_user.stripe_customer_id:
            customer = create_stripe_customer(current_user)
            current_user.stripe_customer_id = customer.id
            db.session.commit()

        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('dashboard', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('pricing', _external=True),
        )
        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, app.config['STRIPE_WEBHOOK_SECRET']
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)

    return 'Success', 200

def handle_checkout_session(session):
    customer_id = session['customer']
    subscription_id = session['subscription']
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if user:
        subscription = create_stripe_subscription(user, subscription_id)
        db.session.add(subscription)
        db.session.commit()

def handle_subscription_updated(subscription):
    user = User.query.filter_by(stripe_customer_id=subscription['customer']).first()
    if user:
        db_subscription = Subscription.query.filter_by(stripe_subscription_id=subscription['id']).first()
        if db_subscription:
            db_subscription.status = subscription['status']
            db_subscription.current_period_end = subscription['current_period_end']
            db.session.commit()

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to edit users.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.subscription_tier = request.form['subscription_tier']
        user.is_admin = 'is_admin' in request.form
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_user.html', user=user)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete users.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/manage_subscription/<int:subscription_id>', methods=['GET', 'POST'])
@login_required
def manage_subscription(subscription_id):
    if not current_user.is_admin:
        flash('You do not have permission to manage subscriptions.', 'danger')
        return redirect(url_for('index'))
    
    subscription = Subscription.query.get_or_404(subscription_id)
    if request.method == 'POST':
        subscription.status = request.form['status']
        subscription.current_period_end = datetime.strptime(request.form['current_period_end'], '%Y-%m-%d')
        db.session.commit()
        flash('Subscription updated successfully.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('manage_subscription.html', subscription=subscription)