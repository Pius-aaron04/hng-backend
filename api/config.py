
import os
class Config:
    """
    Config class that can be used by the flask app to load environment vars
    """

    def __init__(self, env="production"):
        if env == 'development':
            self.SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    
        self.SQLALCHEMY_TRACK_MODIFICATIONS = True
        self.JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
        if env == 'production':
            self.POSTGRES_USER = os.environ.get('POSTGRES_USER')
            self.POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
            self.POSTGRES_DB = os.environ.get('POSTGRES_DB')
            self.POSTGRES_PORT = os.environ.get('POSTGRES_PORT')
            self.SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_DB}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
