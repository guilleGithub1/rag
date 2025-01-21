from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from sqlalchemy.orm import  declarative_base

Base = declarative_base()

class DatabaseManager:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or "postgresql://postgres:postgres@db:5432/mydatabase"
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_database(self):
        try:
            # Importar modelos aquí para que SQLAlchemy los detecte
            from models.resumen import GastoDB, ResumenDB, CuotaDB
            
            # Usar Base global, no self.Base
            Base.metadata.create_all(bind=self.engine)
            
            inspector = inspect(self.engine)
            print(f"Tablas creadas: {inspector.get_table_names()}")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    @contextmanager
    def get_db(self):
        """Proporciona una sesión de base de datos"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_db_dependency():
        """Dependencia para FastAPI"""
        db = DatabaseManager().SessionLocal()
        try:
            yield db
        finally:
            db.close()

    