from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initializing the database
db = SQLAlchemy()

# Admin Table
class Admin(db.Model):
    __tablename__ = 'admin'
    email = db.Column(db.String(120), primary_key=True)
    password = db.Column(db.String(255), nullable=False)

# User Table
class User(db.Model):
    __tablename__ = 'user'
    user_email = db.Column(db.String(120), primary_key=True)
    user_password = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(255), nullable=False)
    qualification = db.Column(db.String(255), nullable=True)
    dob = db.Column(db.Date, nullable=False)

# Subject Table
class Subject(db.Model):
    __tablename__ = 'subject'
    subj_id = db.Column(db.Integer, primary_key=True)
    subj_name = db.Column(db.String(255), nullable=False)
    subj_desc = db.Column(db.String(255), nullable=True)

# Chapter Table
class Chapter(db.Model):
    __tablename__ = 'chapter'
    ch_id = db.Column(db.Integer, primary_key=True)
    ch_name = db.Column(db.String(255), nullable=False)
    ch_desc = db.Column(db.String(255), nullable=True)
    subj_id = db.Column(db.Integer, db.ForeignKey('subject.subj_id'), nullable=False)

# Quiz Table
class Quiz(db.Model):
    __tablename__ = 'quiz'
    quiz_id = db.Column(db.Integer, primary_key=True)
    ch_id = db.Column(db.Integer, db.ForeignKey('chapter.ch_id'), nullable=False)
    subj_id = db.Column(db.Integer, db.ForeignKey('subject.subj_id'), nullable=False)
    date_of_quiz = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.String(5), nullable=False)  # hh:mm format
    remarks = db.Column(db.String(255), nullable=True)

# Questions Table
class Questions(db.Model):
    __tablename__ = 'questions'
    q_id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.quiz_id'), nullable=False)
    subj_id = db.Column(db.Integer, db.ForeignKey('subject.subj_id'), nullable=False)
    ch_id = db.Column(db.Integer, db.ForeignKey('chapter.ch_id'), nullable=False)
    q_title = db.Column(db.String(255), nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correctoption = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4

# Scores Table
class Scores(db.Model):
    __tablename__ = 'scores'
    s_id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.quiz_id'), nullable=False)
    user_email = db.Column(db.String(120), db.ForeignKey('user.user_email'), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    scored = db.Column(db.Integer, nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
