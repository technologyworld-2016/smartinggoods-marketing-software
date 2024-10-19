from app import app, db
from sqlalchemy.exc import OperationalError

def test_db_connection():
    try:
        with app.app_context():
            db.engine.connect()
        print("Database connection successful!")
    except OperationalError as e:
        print(f"Database connection failed: {str(e)}")

if __name__ == "__main__":
    test_db_connection()
