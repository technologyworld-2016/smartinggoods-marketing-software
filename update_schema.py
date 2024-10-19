from app import app, db
from models import User, Subscription
from sqlalchemy import text

def update_schema():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        # Check if the last_login column exists in the User table
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('user')
        column_names = [column['name'] for column in columns]

        if 'last_login' not in column_names:
            # Add the last_login column
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN last_login TIMESTAMP'))
                conn.commit()
            print("Added last_login column to User table.")
        else:
            print("last_login column already exists in User table.")

        print("Database schema updated successfully.")

if __name__ == "__main__":
    update_schema()
