from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Administrator(db.Model):
    __tablename__ = 'administrators'
    a_id = db.Column(db.Integer, primary_key=True)
    a_fname = db.Column(db.String(50), nullable=False)
    a_name = db.Column(db.String(50), nullable=False)
    a_mname = db.Column(db.String(50))
    a_login = db.Column(db.String(50), unique=True, nullable=False)
    a_pass = db.Column(db.String(255), nullable=False)

class Washer(db.Model):
    __tablename__ = 'washers'
    w_id = db.Column(db.Integer, primary_key=True)
    w_fname = db.Column(db.String(50), nullable=False)
    w_name = db.Column(db.String(50), nullable=False)
    w_mname = db.Column(db.String(50))
    w_status = db.Column(db.String(20), default='Свободен') # Свободен, Занят, Перерыв

class Box(db.Model):
    __tablename__ = 'boxes'
    b_id = db.Column(db.Integer, primary_key=True)
    b_status = db.Column(db.String(20), default='Свободен') # Свободен, Занят

class Client(db.Model):
    __tablename__ = 'clients'
    c_id = db.Column(db.Integer, primary_key=True)
    c_fname = db.Column(db.String(50), nullable=False)
    c_name = db.Column(db.String(50), nullable=False)
    c_mname = db.Column(db.String(50))
    c_phone = db.Column(db.String(20), nullable=False)
    c_discount = db.Column(db.Integer, default=0)

class Service(db.Model):
    __tablename__ = 'services'
    s_id = db.Column(db.Integer, primary_key=True)
    s_name = db.Column(db.String(100), nullable=False)
    s_price = db.Column(db.Float, nullable=False)
    s_dur = db.Column(db.Integer, nullable=False) # Duration in minutes

class Discount(db.Model):
    __tablename__ = 'discounts'
    d_id = db.Column(db.Integer, primary_key=True)
    d_marks = db.Column(db.Integer, nullable=False) # Number of visits
    d_perc = db.Column(db.Integer, nullable=False) # Percentage

class Order(db.Model):
    __tablename__ = 'orders'
    o_id = db.Column(db.Integer, primary_key=True)
    o_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    o_status = db.Column(db.String(20), default='В процессе') # В процессе, Завершен, Отменен
    o_cost = db.Column(db.Float, nullable=False)
    
    o_admin = db.Column(db.Integer, db.ForeignKey('administrators.a_id'))
    o_washer = db.Column(db.Integer, db.ForeignKey('washers.w_id'))
    o_box = db.Column(db.Integer, db.ForeignKey('boxes.b_id'))
    o_client = db.Column(db.Integer, db.ForeignKey('clients.c_id'))
    o_discount = db.Column(db.Integer, db.ForeignKey('discounts.d_id'))

    admin = db.relationship('Administrator', backref='orders')
    washer = db.relationship('Washer', backref='orders')
    box = db.relationship('Box', backref='orders')
    client = db.relationship('Client', backref='orders')
    discount = db.relationship('Discount', backref='orders')
