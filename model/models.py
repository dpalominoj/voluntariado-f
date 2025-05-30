from database.db import db
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
import datetime
from flask_login import UserMixin # Import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash # Import hashing functions

# Association table for User (Volunteer) and Activity (Many-to-Many)
volunteer_activities = db.Table('volunteer_activities',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True)
)

class User(db.Model, UserMixin): # Inherit from UserMixin
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Increased length for longer hashes
    role = db.Column(db.String(20), nullable=False, default='Volunteer')  # Roles: Volunteer, Organizer, Admin

    # Relationship for programs organized by this user (if they are an organizer)
    programs = db.relationship('Program', backref='organizer', lazy=True)
    
    # Relationship for activities a user (volunteer) has signed up for
    signed_up_activities = db.relationship('Activity', secondary=volunteer_activities,
                                           backref=db.backref('volunteers', lazy='dynamic'), 
                                           lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Program(db.Model):
    __tablename__ = 'program'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship for activities under this program
    activities = db.relationship('Activity', backref='program', lazy=True)

    def __repr__(self):
        return f'<Program {self.name}>'

class Activity(db.Model):
    __tablename__ = 'activity'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=True, default=datetime.datetime.utcnow)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)

    def __repr__(self):
        return f'<Activity {self.name} on {self.date}>'
