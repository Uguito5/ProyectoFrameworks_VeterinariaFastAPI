from database import SessionLocal
import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def crear_admin():
    db = SessionLocal()
    # Verifica si ya existe
    admin_existente = db.query(models.Usuario).filter(models.Usuario.cedula == "admin").first()
    
    if not admin_existente:
        password_cifrada = pwd_context.hash("admin123") # Cambia esta contraseña
        nuevo_admin = models.Usuario(
            cedula="admin", 
            password_hash=password_cifrada, 
            rol="admin"
        )
        db.add(nuevo_admin)
        db.commit()
        print("¡Superusuario 'admin' creado exitosamente!")
    else:
        print("El superusuario ya existe.")
    
    db.close()

if __name__ == "__main__":
    crear_admin()