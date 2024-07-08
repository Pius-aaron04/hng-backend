"""
Defines Models for User and Organisation
"""

from sqlalchemy import String, Column, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4

Base = declarative_base()

class BaseModel:
    """
    Base model class that contains common methods
    """

    def save(self):
        """
        saves object to the data base
        """

        from .app import storage
        try:
            storage.new(self)
            storage.save()
        except Exception:
            storage.rollback()

    def delete(self):
        """
        deletes object from the data base
        """

        from .app import storage
        if self.__class__ == User:
            for org in self.organisations:
                storage.delete(org)
        storage.delete(self)
        storage.save()

class User(BaseModel, Base):
    """
    Defines user model with data fields
    """
    __tablename__ = "users"

    userId = Column(String(60), default=str(uuid4()), nullable=False,
                    primary_key=True, unique=True)
    orgId = Column(String(60), ForeignKey("organisations.orgId"), nullable=True)
    firstName = Column(String(60), nullable=False)
    lastName = Column(String(60), nullable=False)
    email = Column(String(60), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    phone = Column(String(50))
    organisations = relationship("Organisation", secondary="user_organisation", backref="users", lazy="dynamic")

    def __init__(self, **kwargs):
        from .app import bcrypt

        """
        Initializes User
        """
        for k, v in kwargs.items():
            if k != "password":
                setattr(self, k, v)
            else:
                self.password = bcrypt.generate_password_hash(v).decode('utf-8')

    def __repr__(self):
        return f'<User {self.userId}>'

    def to_dict(self):
        """
        Returns user data in dictionary format
        """
        return {
            "userId": self.userId,
            "firstName": self.firstName,
            "lastName": self.lastName,
            "email": self.email,
            "phone": self.phone
        }


class Organisation(BaseModel, Base):
    """
    Defines organisation model with data fields
    """
    __tablename__ = "organisations"
    orgId = Column(String(60), default=str(uuid4()), nullable=False,
                    primary_key=True, unique=True)
    userId = Column(String(60), ForeignKey("users.userId"), nullable=True)
    name = Column(String(50), nullable=False)
    description = Column(String(128))


    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        
    def __repr__(self):
        return f'<Organisation {self.orgId}>'
    
    def to_dict(self):
        """
        Returns organisation data in dictionary format
        """
        return {
            "orgId": self.orgId,
            "name": self.name,
            "description": self.description
        }


user_organisation = Table('user_organisation', Base.metadata,
                        Column('user_id', String(60),
                               ForeignKey('users.userId'), primary_key=True),
                        Column('organisation_id', String(60),
                               ForeignKey('organisations.orgId'), primary_key=True)
                        )
