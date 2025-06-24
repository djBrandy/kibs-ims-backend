from app import app
from app.database import db, migrate
from flask.cli import FlaskGroup # type: ignore

def create_app():
    return app

cli = FlaskGroup(create_app=create_app)

if __name__ == '__main__':
    cli()
