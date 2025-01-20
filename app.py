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
        try:
            data = request.get_json()
            
            # Check if required fields are present
            if not data or 'email' not in data or 'password' not in data:
                return jsonify({
                    'message': 'Email and password are required'
                }), 400

            user = user_datastore.find_user(email=data['email'])
            
            if not user:
                return jsonify({
                    'message': 'Invalid credentials'
                }), 401

            if not user.active:
                return jsonify({
                    'message': 'Account is not active. Please wait for admin approval.'
                }), 401

            if not verify_password(data['password'], user.password):
                return jsonify({
                    'message': 'Invalid credentials'
                }), 401

            # Successful login
            login_user(user)
            auth_token = user.get_auth_token()
            return jsonify({
                'access_token': auth_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'roles': [{'name': role.name} for role in user.roles]
                }
            }), 200

        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            return jsonify({
                'message': 'An unexpected error occurred. Please try again later.'
            }), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
