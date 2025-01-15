from flask_security import SQLAlchemySessionUserDatastore
from extensions import db
from flask_security.utils import hash_password



def create_data(user_datastore : SQLAlchemySessionUserDatastore):
    print("creating roles and users") # for debug purposes

    # creating roles

    user_datastore.find_or_create_role(name='admin', description = "Administrator")
    
    user_datastore.find_or_create_role(name='user', description = "User")

    # creating initial data

    if not user_datastore.find_user(email = "admin@iitm.ac.in"):
        user_datastore.create_user(email = "admin@iitm.ac.in", password = hash_password("pass"), roles=['admin'])
    if not user_datastore.find_user(email = "user@iitm.ac.in"):
        user_datastore.create_user(email = "user@iitm.ac.in", password = hash_password("pass"), roles=['user'])

    # create dummy resource

    db.session.commit()
