from app import app, db
from flask_migrate import Migrate # type: ignore
from flask.cli import FlaskGroup # type: ignore

migrate = Migrate(app, db)

def create_app():
    return app

cli = FlaskGroup(create_app=create_app)

if __name__ == '__main__':
    cli()
