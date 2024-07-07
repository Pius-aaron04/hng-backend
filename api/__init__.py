"""
Flask api app
"""

from .storage_engine import DBStorage

storage = DBStorage()

storage.reload()
