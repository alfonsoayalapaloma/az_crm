from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.orm import validates

from app import db

class Person(db.Model):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('company.id', ondelete="CASCADE"))    
    street_address = Column(String(255))
    facility_name= Column(String(255))  
    name = Column(String(128))
    phone =Column(String(128))
    email =Column(String(128))
    contact_type=Column(String(128))
    modification_date = Column(DateTime)
        
    def __str__(self):
        return f"{self.id}: {self.name} "

class Company(db.Model):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    name=Column(String(255))    
    street_address = Column(String(255))
    description = Column(String(250))

    def __str__(self):
        return f"{self.id}: {self.name} "