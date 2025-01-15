from flask import Flask, request, jsonify
from extensions import db
import views
import create_initial_data
import resources
from flask_security import auth_required, Security, login_user
from flask_security.utils import verify_password

def create_app():
    app = Flask(__name__)

    # configuration
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'NbrKrOgSTkiVDItpfQzjF6UuX0jNJcuwTKX6MypiCJQ'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
    app.config['SECURITY_PASSWORD_SALT'] = '9RrPTYTgV4c-iFafQeB7RQ'
    app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication-Token'
    

    # tell flask to use sql_alchemy db
    db.init_app(app)

    with app.app_context():
        from models import User, Role
        from flask_security import SQLAlchemyUserDatastore

        user_datastore = SQLAlchemyUserDatastore(db, User, Role)
        security = Security(app, user_datastore)
        
        db.create_all()
        create_initial_data.create_data(user_datastore)

        
    # enable CSRF protection
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True
    app.config['SECURITY_CSRF_PROTECT_MECHANISMS'] = ['session', 'token']
    app.config['SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS'] = False

    # setup the view
    views.create_views(app, user_datastore, db)

    # setup api
    resources.api.init_app(app)

    @app.route('/', methods=['POST'])
    def login():
        data = request.get_json()
        user = user_datastore.find_user(email=data['email'])
        if user and verify_password(data['password'], user.password):
            login_user(user)
            auth_token = user.get_auth_token()
            return jsonify({'access_token': auth_token, 'user': {'id': user.id, 'email': user.email, 'roles': [role.name for role in user.roles]}}), 200
        return jsonify({'message': 'Invalid credentials'}), 401

    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
