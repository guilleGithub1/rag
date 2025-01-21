
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from datetime import date
from config.database import Base


# Modelo para la base de datos

class ResumenDB(Base):
    __tablename__ = "resumenes"

    id = Column(Integer, primary_key=True, index=True)
    emision = Column(Date)
    vencimiento = Column(Date)
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    marca = Column(String)
    # Relación correcta con gastos
    gastos = relationship("GastoDB", back_populates="resumen")
    bancos = relationship("BancoDB", back_populates="resumenes")



class GastoDB(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date)
    comercio = Column(String)
    monto = Column(Float)
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

class BancoDB(Base):
    __tablename__ = "bancos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    patron_busqueda = Column(String)  # Cambiado de re_busqueda a patron_busqueda
    resumenes = relationship("ResumenDB", back_populates="bancos")
    subject = Column(String)
    sender = Column(String)
    visa = Column(Boolean, default=False)
    mastercard=  Column(Boolean, default=False)
    amex=  Column(Boolean, default=False)







# Modelo para la API (Pydantic)
class Resumen(BaseModel):
    id: Optional[int] = None
    emision: date
    vencimiento: date
    banco: str
    marca: str

class MailResumen(BaseModel):
    subject: str
    sender: str


class Banco(BaseModel):
    nombre: str
    patron_busqueda: str
    subject: str
    sender: str
    visa: bool
    mastercard: bool
    amex: bool

