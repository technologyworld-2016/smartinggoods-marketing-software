import os

def check_config():
    with open('config.py', 'r') as f:
        print("Contents of config.py:")
        print(f.read())

def check_env_var():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print("\nDATABASE_URL is set.")
        print(f"DATABASE_URL value: {database_url[:10]}...{database_url[-10:]}")  # Print first and last 10 characters
    else:
        print("\nDATABASE_URL is not set.")

if __name__ == "__main__":
    check_config()
    check_env_var()
