from app import app, db
from models import User, Subscription, UserSession, SubscriptionPlan
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

def update_schema():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        # Check if the last_login column exists in the User table
        inspector = db.inspect(db.engine)
        user_columns = inspector.get_columns('user')
        user_column_names = [column['name'] for column in user_columns]

        if 'last_login' not in user_column_names:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN last_login TIMESTAMP'))
                conn.commit()
            print("Added last_login column to User table.")
        
        if 'created_at' not in user_column_names:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
                conn.commit()
            print("Added created_at column to User table.")

        if 'is_admin' not in user_column_names:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN is_admin BOOLEAN DEFAULT FALSE'))
                conn.commit()
            print("Added is_admin column to User table.")

        # Check if the amount and created_at columns exist in the Subscription table
        subscription_columns = inspector.get_columns('subscription')
        subscription_column_names = [column['name'] for column in subscription_columns]

        if 'amount' not in subscription_column_names:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE subscription ADD COLUMN amount FLOAT'))
                conn.commit()
            print("Added amount column to Subscription table.")
        
        if 'created_at' not in subscription_column_names:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE subscription ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
                conn.commit()
            print("Added created_at column to Subscription table.")

        # Check if the stripe_price_id column exists in the SubscriptionPlan table
        subscription_plan_columns = inspector.get_columns('subscription_plan')
        subscription_plan_column_names = [column['name'] for column in subscription_plan_columns]

        if 'stripe_price_id' not in subscription_plan_column_names:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE subscription_plan ADD COLUMN stripe_price_id VARCHAR(50) UNIQUE'))
                conn.commit()
            print("Added stripe_price_id column to SubscriptionPlan table.")

        # Create UserSession table if it doesn't exist
        if not inspector.has_table('user_session'):
            try:
                UserSession.__table__.create(db.engine)
                print("Created UserSession table.")
            except ProgrammingError:
                print("UserSession table already exists.")

        print("Database schema updated successfully.")

if __name__ == "__main__":
    update_schema()
