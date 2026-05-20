from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base 


class Dueno(Base):
    __tablename__ = "duenos"

    id = Column(Integer, primary_key=True, index=True)
    cedula = Column(String, unique=True, index=True, nullable=False) # Única para evitar duplicados de personas
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    direccion = Column(String, nullable=True)
    telefono = Column(String, nullable=True) 
    correo = Column(String, nullable=True)
    fecha_registro = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)

    # Relación inversa: permite hacer `dueno.mascotas` y obtener su lista automáticamente
    mascotas = relationship("Mascota", back_populates="dueno", cascade="all, delete-orphan")
    usuario = relationship(
        "Usuario", 
        primaryjoin="foreign(Dueno.cedula) == Usuario.cedula",
        back_populates="dueno", 
        uselist=False
    )

class Mascota(Base):
    __tablename__ = "mascotas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    especie = Column(String)
    raza = Column(String)
    edad = Column(Integer)
    dueno_id = Column(Integer, ForeignKey("duenos.id", ondelete="CASCADE"), nullable=False)
    observaciones = Column(String, default="Sin observaciones") # <-- Nuevo campo
    
    
    dueno = relationship("Dueno", back_populates="mascotas")
    examenes = relationship("Examen", back_populates="mascota", cascade="all, delete-orphan")
    recetas = relationship("Receta", back_populates="mascota", cascade="all, delete-orphan")
    facturas = relationship("Factura", back_populates="mascota", cascade="all, delete-orphan")

class Factura(Base):
    __tablename__ = "facturas"
    id = Column(Integer, primary_key=True, index=True)
    servicio = Column(String)
    monto = Column(Float)
    fecha = Column(DateTime, default=datetime.now)
    
    #llave foranea hacia mascota
    mascota_id = Column(Integer, ForeignKey("mascotas.id", ondelete="CASCADE"), nullable=False)
    
    mascota = relationship("Mascota", back_populates="facturas")

class Examen(Base):
    __tablename__ = "examenes"
    
    id = Column(Integer, primary_key=True, index=True)
    mascota_id = Column(Integer, ForeignKey("mascotas.id"))
    titulo = Column(String)
    resultado = Column(String)
    
    # Relación
    mascota = relationship("Mascota", back_populates="examenes")

class Receta(Base):
    __tablename__ = "recetas"
    
    id = Column(Integer, primary_key=True, index=True)
    mascota_id = Column(Integer, ForeignKey("mascotas.id"))
    medicamento = Column(String)
    indicaciones = Column(String)
    
    # Relación
    mascota = relationship("Mascota", back_populates="recetas")

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    cedula = Column(String, unique=True, index=True) # El login será con la cédula
    password_hash = Column(String)
    rol = Column(String, default="user") # "admin" o "user"

    dueno = relationship(
        "Dueno", 
        primaryjoin="Usuario.cedula == foreign(Dueno.cedula)", 
        foreign_keys="Dueno.cedula",
        back_populates="usuario", 
        uselist=False
    )