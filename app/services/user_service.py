from app.models.user import User
from app import db, bcrypt

def create_user(data, profile_picture='default.jpg'):
    if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
        return None
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hashed_password,
        profile_picture=profile_picture
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()