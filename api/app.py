"""
Flask api app
"""

from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from .models import User, Organisation
from flask_jwt_extended import (JWTManager, jwt_required, create_access_token, get_jwt_identity)
from flask_cors import CORS
import os
from .config import Config
from . import storage
import datetime
from uuid import uuid4


config = Config
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # avoids warning
app.config['SQLALCHEMY_MIGRATE_WITH_SCHEMA'] = True
app.config['SQLALCHEMY_MIGRATE_WITH_MISSING'] = True
migrate = Migrate(app, storage.engine)

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
bcrypt = Bcrypt(app)

jwt = JWTManager(app)
jwt.jwt_payload_handler = lambda identity: {'identity': identity, 'exp': datetime.datetime.now() + datetime.timedelta(hours=24)}
jwt.jwt_expires_delta = datetime.timedelta(hours=24)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/", strict_slashes=False)
def index():
    return "Hello"

@app.route("/auth/register", methods=["POST"], strict_slashes=False)
def register():
    """
    Register user
    """
    
    payload = request.get_json()
    if not payload:
        return jsonify({
            "errors":[
                {
                    "message": "No data provided"
                }
            ]
            }), 422
    if not payload.get("firstName"):
        return jsonify({
            "errors": [{
                "field": "firstName",
               "message": "First name is required"
               }
            ]
            }), 422
    if not payload.get("lastName"):
        return jsonify({
            "errors": [{
                "field": "lastName",
               "message": "Last name is required"
               }
            ]
        }), 422
    if not payload.get("email"):
        return jsonify({
            "errors": [{
                "field": "email",
               "message": "Email is required"
               }
            ]
        }), 422
    if not payload.get("password"):
        return jsonify({
            "errors":[
                {
                    "field": "password",
                    "message": "password required"
                }
            ]
        }), 422

    # check if user exists
    user = storage.fetch(User, limit=1, email=payload["email"])
    if user:
        return jsonify({
            "status": "Bad request",
            "message": "Registration failed",
            "statusCode": 400
        }), 400
    
    # create user
    payload['userId'] = str(uuid4())
    user = User(**payload)
    # create an organisation object by default with user's first name as name
    org_name = user.firstName + "'s organisation"
    org = Organisation(name=org_name, orgId=user.userId)
    org.save()
    user.organisations.append(org)
    user.save()

    # generate jwt token
    token = create_access_token(identity=user.userId)
    success = {
        "status": "success",
        "message": "Registration successful",
        "data":{
            "accessToken": token,
            "user": user.to_dict(),
        }
    }

    return jsonify(success), 201


@app.route("/auth/login", methods=["POST"], strict_slashes=False)
def login():
    """
    Login user
    """

    failure_res = {
            "status": "Bad request",
            "message": "authentication failed",
            "statusCode": 400}

    payload = request.get_json()
    if "email" not in payload or "password" not in payload:
        return jsonify(failure_res), 400

    # fetch user object with matching email
    user = storage.fetch(User, limit=1, email=payload["email"])
    if not user:
        return jsonify(failure_res), 401
    if not bcrypt.check_password_hash(user.password, payload["password"]):
        return jsonify(failure_res), 401

    # return user object in dictionary format with jwt_token
    token = create_access_token(identity=user.userId)
    success = {
        "status": "success",
        "message": "Login successful",
        "data":{
            "accessToken": token,
            "user": user.to_dict(),
        }
    }
    return success, 200


@app.route("/api/users/<id>", strict_slashes=False)
@jwt_required()
def user(id):
    """
    Get user by id"""

    identity = get_jwt_identity()
    user = None
    if identity:
        user = storage.fetch(User, limit=1, userId=identity)

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.userId == id:
        return {
            "success": "success",
            "message": "User retrieved successfully",
            "data": user.to_dict()
        }, 200
    
    other_user = storage.fetch(User, limit=1, userId=id)
    if not other_user:
        return jsonify({"message": "User not found"}), 404
    for org in user.organisations:
        if other_user in org.users:
            return {
                "success": "success",
                "message": "User retrieved successfully",
                "data": other_user.to_dict()
            }, 200

    return {"message": "Unauthorized"}, 401

# yet to be implemented [Portected]
@app.route("/api/organisations", strict_slashes=False, methods=["GET"])
@jwt_required()
def get_user_organisations():
    """
    Get all organisations for a user
    """

    identity = get_jwt_identity()

    if not identity:
        return {"message": "Unauthorized"}, 401

    user = storage.fetch(User, limit=1, userId=identity)

    if user:
        success = {
            "satus": "success",
            "message": "Organisations retrieved successfully",
            "data": {
                "organisations": [org.to_dict() for org in user.organisations]
                }
        }

        return success, 200

    return {"error": "User not found"}, 404

@app.route("/api/organisations/<orgId>", strict_slashes=False, methods=["GET"])
@jwt_required()
def get_organisation(orgId):
    """
    Get organisation by id
    """

    userId = get_jwt_identity()

    org = storage.fetch(Organisation, limit=1, orgId=orgId)

    if not org or org.userId != userId:
        return {"message": "Unauthorized"}, 401

    return {"success": "success",
            "message": "Organisation retrieved successfully",
            "data": org.to_dict()
            }, 200
    

@app.route("/api/organisations", strict_slashes=False, methods=["POST"])
@jwt_required()
def create_organisation():
    """
    Create organisation
    """

    user = storage.fetch(User, limit=1, userId=get_jwt_identity())
    if not user:
        return {"message": "Unauthorized"}, 401
    
    payload = request.get_json()

    if "name" not in payload:
        return {
            "status": "Bad request",
            "message": "Client error",
            "statusCode": 400
        }, 400
    
    payload["orgId"] = str(uuid4())
    org = Organisation(**payload)
    org.userId = user.userId
    if org in user.organisations:
        return {"message": "Organisation already exists"}, 400
    user.organisations.append(org)
    org.save()

    return {"success": "success",
            "message": "Organisation created successfully",
            "data": org.to_dict()
            }, 201


@app.route("/api/organisations/<orgId>/users",
           strict_slashes=False, methods=["POST"])
def add_user_to_organisation(orgId):
    """
    Add user to organisation
    """

    org = storage.fetch(Organisation, limit=1, orgId=orgId)
    payload = request.get_json()

    if not any((org, payload)):
        return {"message": "Bad request"}, 400
    
    user = storage.fetch(User, limit=1, userId=payload["userId"])
    if user in org.users:
        return {"message": "User already in organisation"}, 400
    org.users.append(user)
    org.save()

    return {"success": "success",
            "message": "User added to organisation successfully",
            }, 200


if __name__ == '__main__':
    app.run()
