from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String, nullable=False) 
    image_url = db.Column(db.String)
    bio = db.Column(db.String)

    recipes = db.relationship(
        'Recipe',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    serialize_only = ('id', 'username', 'image_url', 'bio')

    @property
    def password_hash(self):
        raise AttributeError("Password hash is write-only.")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates('username')
    def validate_username(self, key, value):
        if not value or value.strip() == '':
            raise ValueError("Username must be present.")
        return value.strip()

    def __init__(self, **kwargs):
        password = kwargs.pop("password", None)
        super().__init__(**kwargs)
        if not self._password_hash:
            self.password_hash = password or "defaultpassword"

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    serialize_only = ('id', 'title', 'instructions', 'minutes_to_complete', 'user_id')

    @validates('title')
    def validate_title(self, key, value):
        if not value or value.strip() == '':
            raise ValueError("Title must be present.")
        return value.strip()

    @validates('instructions')
    def validate_instructions(self, key, value):
        value = value.strip()
        if not value:
            raise ValueError("Instructions must be present.")
        if len(value) < 50:
            raise ValueError("Instructions must be at least 50 characters long.")
        return value

    @validates('minutes_to_complete')
    def validate_minutes(self, key, value):
        if value is not None and value < 1:
            raise ValueError("Minutes must be a positive number.")
        return value

    @validates('user_id')
    def validate_user_id(self, key, value):
        if value is None:
            raise ValueError("Recipe must belong to a user.")
        return value