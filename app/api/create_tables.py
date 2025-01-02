from config.database import engine, Base
from models.resumen import GastoDB, ResumenDB, CuotaDB

# Crea todas las tablas en la base de datos
Base.metadata.create_all(bind=engine)