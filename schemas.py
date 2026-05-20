from pydantic import BaseModel

# Esquema para crear una mascota (lo que envía el usuario)
class MascotaCreate(BaseModel):
    nombre: str
    especie: str
    raza: str
    edad: int
    nombre_dueno: str

# Esquema para mostrar una mascota (lo que responde el sistema)
class MascotaResponse(MascotaCreate):
    id: int

    class Config:
        from_attributes = True