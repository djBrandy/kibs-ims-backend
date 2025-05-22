import os
import sys

# Add the current directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the migration script
from add_hidden_column import add_hidden_column

if __name__ == "__main__":
    print("Running database migration...")
    add_hidden_column()
    print("Migration complete. Please restart your Flask application.")