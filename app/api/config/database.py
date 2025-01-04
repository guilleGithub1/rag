from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or "postgresql://postgres:postgres@db:5432/mydatabase"
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()

    def create_database(self):
        """Crea todas las tablas definidas"""
        try:
            self.Base.metadata.create_all(bind=self.engine)
            return True
        except Exception as e:
            print(f"Error al crear la base de datos: {e}")
            return False

    @contextmanager
    def get_db(self):
        """Proporciona una sesión de base de datos"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_db_dependency(self):
        """Dependencia para FastAPI"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
