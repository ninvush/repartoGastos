from flask import Flask
from config import Config
from extensions import conexion, mail

from routes.auth_routes import auth_bp
from routes.group_routes import group_bp
from routes.expense_routes import expense_bp
from routes.debt_routes import debt_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    conexion.init_app(app)
    mail.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(debt_bp)

    return app


app = create_app()


if __name__ == '__main__':
    app.run()