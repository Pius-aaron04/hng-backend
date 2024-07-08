import os
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import User, Organisation, Base


class DBStorage:
    """
    Database storage engine
    accesses database, manipulates and returns data
    """

   
    classes = {
        "User": User,
        "Organisation": Organisation
    }

    @property
    def engine(self):
        return self.__engine

    def __init__(self):

        connection_string = URL.create('postgresql',
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            database=os.getenv('POSTGRES_DB')
        ) 
        ENV = os.getenv('FLASK_ENV')
        if ENV == "development" or ENV == "test":
            self.__engine = create_engine('sqlite:///database.db')
        elif ENV == "production":
            self.__engine = create_engine(connection_string)


    def fetch(self, cls, limit=None,**kwargs):
        """
        fectchs object by kwargs
        """
        try:
            if limit:
                return self.__session.query(cls).filter_by(**kwargs).limit(limit).first()
            else:
                return self.__session.query(cls).filter_by(**kwargs).all()
        except Exception:
            self.rollback()

    def reload(self):
        """
        Reloads the database
        """

        # Create the tables
        Base.metadata.create_all(self.__engine)

        # Create a session
        session = sessionmaker(bind=self.__engine, expire_on_commit=False)
        self.__session = scoped_session(session)

    def save(self):
        """
        saves data to database
        """

        self.__session.commit()

    def close(self):
        """
        closes database
        """

        self.__session.close()
    
    def new(self, obj):
        """
        Adds new object to database
        """

        self.__session.add(obj)
    
    def delete(self, obj=None):
        """
        removes an object from database.
        """

        if obj and obj in self.fetch(obj.__class__):
            self.__session.delete(obj)

    def rollback(self):
        """
        rollback database if faiure occurs during flush
        """

        self.__session.rollback()
