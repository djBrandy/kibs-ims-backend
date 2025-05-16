# manage.py
from app import app, db
from flask_migrate import Migrate
import flask_migrate
import os
import shutil

# Create the migrate extension
migrate_extension = Migrate(app, db)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'run':
            app.run(host='0.0.0.0', port=5000, debug=True)
            
        elif command == 'db':
            if len(sys.argv) > 2:
                subcommand = sys.argv[2]
                
                with app.app_context():
                    if subcommand == 'init':
                        flask_migrate.init()
                        print("Database migrations initialized.")
                    
                    elif subcommand == 'migrate':
                        message = "Migration"
                        if len(sys.argv) > 4 and sys.argv[3] == '-m':
                            message = sys.argv[4]
                        flask_migrate.migrate(message=message)
                        print(f"Migration created with message: {message}")
                    
                    elif subcommand == 'upgrade':
                        flask_migrate.upgrade()
                        print("Database upgraded.")
                    
                    elif subcommand == 'reset':
                        # Drop all tables
                        db.drop_all()
                        
                        # Remove migrations directory
                        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
                        if os.path.exists(migrations_dir):
                            shutil.rmtree(migrations_dir)
                            print("Removed migrations directory.")
                        
                        # Initialize migrations
                        flask_migrate.init()
                        print("Migrations reset successfully.")
                    
                    elif subcommand == 'fix':
                        # Execute SQL to drop the alembic_version table
                        with db.engine.connect() as conn:
                            conn.execute("DROP TABLE IF EXISTS alembic_version")
                        print("Dropped alembic_version table.")
                        
                        # Remove migrations directory
                        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
                        if os.path.exists(migrations_dir):
                            shutil.rmtree(migrations_dir)
                            print("Removed migrations directory.")
                        
                        # Initialize migrations
                        flask_migrate.init()
                        print("Migration history fixed. Now run 'python manage.py db migrate -m \"Initial migration\"'")
                    
                    else:
                        print(f"Unknown subcommand: {subcommand}")
                        print("Available subcommands: init, migrate, upgrade, reset, fix")
            else:
                print("Missing subcommand for db")
                print("Available subcommands: init, migrate, upgrade, reset, fix")
        else:
            print(f"Unknown command: {command}")
    else:
        print("Usage: python manage.py [run|db]")
        print("For database commands: python manage.py db [init|migrate|upgrade|reset|fix]")
