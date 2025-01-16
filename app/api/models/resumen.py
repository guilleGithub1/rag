
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from datetime import date
from config.database import Base


# Modelo para la base de datos

class ResumenDB(Base):
    __tablename__ = "resumenes"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date)
    banco = Column(String)
    marca = Column(String)
    # Relación correcta con gastos
    gastos = relationship("GastoDB", back_populates="resumen")


class GastoDB(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date)
    comercio = Column(String)
    monto = Column(Float)
    banco = Column(String)
    marca = Column(String)
    resumen_id = Column(Integer, ForeignKey("resumenes.id"))


    # Relaciones bidireccionales
    resumen = relationship("ResumenDB", back_populates="gastos")
    cuotas = relationship("CuotaDB", back_populates="gasto")

class CuotaDB(Base):
    __tablename__ = "cuotas"

    id = Column(Integer, primary_key=True, index=True)
    cantidad_cuotas = Column(Integer)
    numero_cuota_pagada = Column(Integer)
    gasto_id = Column(Integer, ForeignKey("gastos.id")) # Foreign key to GastoDB

    # Relación con gasto
    gasto = relationship("GastoDB", back_populates="cuotas")




# Modelo para la API (Pydantic)
class Resumen(BaseModel):
    id: Optional[int] = None
    emision: date
    vencimiento: date
    banco: str
    marca: str