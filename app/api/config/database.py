from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# URL de conexión a la base de datos (ajusta según tu configuración)
DATABASE_URL = "postgresql://usuario:contraseña@host:5432/nombre_de_la_base_de_datos"
# Ejemplo:
# DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mydatabase"

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Crear una clase base para los modelos
Base = declarative_base()


# Crear una clase para manejar las sesiones de la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


#Función para obtener una sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
      yield db
    finally:
      db.close()


#Función para crear las tablas de la base de datos
def create_database():
  Base.metadata.create_all(bind=engine)