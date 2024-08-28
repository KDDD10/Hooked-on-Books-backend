import os
# from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app import db, bcrypt
from app.models.user import User
from app.services.user_service import create_user, get_user_by_username
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask import Blueprint, request, jsonify, current_app, send_from_directory, url_for

bp = Blueprint('auth', __name__)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/register', methods=['POST'])
def register():
    if request.content_type.startswith('multipart/form-data'):
        data = request.form
    elif request.content_type.startswith('application/json'):
        data = request.get_json()
    else:
        return jsonify({"message": "Unsupported Content-Type"}), 415

    if not data:
        return jsonify({"message": "Invalid request data"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"message": "Missing required fields"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"message": "Username or email already exists"}), 400

    profile_picture = 'default.jpg'
    if request.files and 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_extension = os.path.splitext(filename)[1]
            new_filename = f"user_{username}{file_extension}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename))
            profile_picture = new_filename

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password_hash=hashed_password, profile_picture=profile_picture)
    
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=new_user.id)

    profile_picture_url = url_for('auth.serve_profile_pic', filename=profile_picture, _external=True) if profile_picture != 'default.jpg' else url_for('static', filename='images/default.jpg', _external=True)

    return jsonify({
        "message": "User registered successfully",
        "success": True,
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "profile_picture": profile_picture_url,
            "date_joined": new_user.date_joined.isoformat()
        },
        "access_token": access_token
    }), 201
# Make sure to add this route to serve profile pictures
@bp.route('/profile_pic/<filename>')
def serve_profile_pic(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = get_user_by_username(data.get('username'))
    if user and bcrypt.check_password_hash(user.password_hash, data.get('password')):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify({"message": "Invalid username or password"}), 401

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # In a stateless JWT setup, the client is responsible for discarding the token
    return jsonify({"message": "Logout successful"}), 200

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user:
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "date_joined": user.date_joined.isoformat()
        }), 200
    return jsonify({"message": "User not found"}), 404


