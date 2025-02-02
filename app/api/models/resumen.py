
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
    mail_id = Column(Integer, ForeignKey("mails.id"))
    marca = Column(String)
    # Relación correcta con gastos
    gastos = relationship("GastoDB", back_populates="resumenes")
    bancos = relationship("BancoDB", back_populates="resumenes")
    mail= relationship("MailDB", back_populates="resumenes")



class GastoDB(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date)
    comercio = Column(String)
    monto = Column(Float)
    marca = Column(String)
    moneda = Column(String)
    resumen_id = Column(Integer, ForeignKey("resumenes.id"))

    # Relaciones bidireccionales
    resumen = relationship("ResumenDB", back_populates="gastos")
    cuotas = relationship("CuotaDB", back_populates="gastos")

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
    patron_link_descarga = Column(String)
    subject = Column(String)
    sender = Column(String)
    archivo_adjunto= Column(Boolean)
    patrones_visa = Column(Integer, ForeignKey("patrones.id"))
    patrones_amex = Column(Integer, ForeignKey("patrones.id"))
    patrones_mastercard = Column(Integer, ForeignKey("patrones.id"))
    
    # Relaciones específicas por tipo de tarjeta
    patron_visa = relationship("PatronDB", foreign_keys=[patrones_visa])
    patron_amex = relationship("PatronDB", foreign_keys=[patrones_amex])
    patron_mastercard = relationship("PatronDB", foreign_keys=[patrones_mastercard])



    # Relación con resumenes    
    resumenes = relationship("ResumenDB", back_populates="bancos")

class PatronDB(Base):
    __tablename__ = "patrones"

    id = Column(Integer, primary_key=True, index=True)
    transacion = Column(String)
    transaccion_cuota = Column(String)
    fecha_cierre = Column(String)
    fecha_vencimiento = Column(String)
    descripcion = Column(String)
    ancho_maximo = Column(Integer)


class MailDB(Base):
    __tablename__ = "mails"

    id = Column(Integer, primary_key=True, index=True)
    mail_gmail_id = Column(Integer)
    fecha = Column(Date)
    contenido_mail = Column(String,nullable=True)

    # Relación con resumenes
    resumenes = relationship("ResumenDB", back_populates="mail")
    resumenes_pdf = relationship("AdjuntoDB", back_populates="mail")   

class ResumenPdfDB(Base):
    __tablename__ = "resumenes_pdf"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String,nullable=True)
    mail_id = Column(Integer, ForeignKey("mails.id"))
    link_descarga = Column(String,nullable=True)
    contenido_pdf = Column(String,nullable=True)

    # Relación con mail
    mail = relationship("MailDB", back_populates="resumenes_pdf")


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
    patrones_visa: Optional[int] = None
    patrones_amex: Optional[int] = None
    patrones_mastercard: Optional[int] = None



class Patron(BaseModel):
    descripcion: str
    transaccion: str
    transaccion_cuota: str
    fecha_cierre: str
    fecha_vencimiento: str
    ancho_maximo: int

