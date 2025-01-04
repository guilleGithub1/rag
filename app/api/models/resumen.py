from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from datetime import date
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional
# Modelo para la base de datos
Base = declarative_base()
# Modelo para la base de datos
class GastoDB(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date)
    comercio = Column(String)
    monto= Column(Integer)
    banco= Column(String)
    marca = Column(String)
    resumen_id = Column(Integer, ForeignKey("resumenes.id"))
    cuota_id = Column(Integer, ForeignKey("cuotas.id"))

class ResumenDB(Base):
    __tablename__ = "resumenes"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date)
    banco= Column(String)
    marca = Column(String)

class CuotaDB(Base):
    __tablename__ = "cuotas"

    id = Column(Integer, primary_key=True, index=True)
    cantidad_cuotas = Column(Integer)
    numero_cuota_pagada  = Column(Integer)



# Modelo para la API (Pydantic)
class Resumen(BaseModel):
    id: Optional[int] = None
    fecha: date
    banco: str
    marca: str