from datetime import datetime, timedelta
from jose import jwt
from jose import JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import aiosmtplib
from email.message import EmailMessage
from fastapi import FastAPI, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas, database
import re
from fastapi import BackgroundTasks
from utils import generar_pdf_buffer, generar_pdf_desde_html
from passlib.context import CryptContext

# Crea las tablas en la base de datos de manera automática
models.Base.metadata.create_all(bind=database.engine)


#1 Función para enviar correo 
async def enviar_correo_directo(destinatario: str, asunto: str, cuerpo: str, pdf_buffer):
    mensaje = EmailMessage()
    mensaje["From"] = "roesvet@hotmail.com"
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)
    
    # IMPORTANTE: PDF_BUFFER.GETVALUE() extrae los bytes del objeto BytesIO
    mensaje.add_attachment(
        pdf_buffer.getvalue(), 
        maintype="application",
        subtype="pdf",
        filename="reporte.pdf"
    )

    # Configuración de Mailtrap
    await aiosmtplib.send(
        mensaje,
        hostname="sandbox.smtp.mailtrap.io", # El host Mailtrap
        port=2525,                          # El puerto Mailtrap
        username="79f12b286b0492",      # usuario de Mailtrap
        password="431a1ecfa968d3",  # contraseña de Mailtrap
        use_tls=False,    
        start_tls=False
    )
app = FastAPI()

# Configuración de carpetas para la interfaz visual
templates = Jinja2Templates(directory="templates")

# Función para conectar con la base de datos
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
''' aqui va el login 
@app.get("/")
async def root():
    # Redirige automáticamente al usuario a la pantalla de login
    return RedirectResponse(url="/login")

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Define cuánto tiempo durará la sesión (ej. 30 minutos)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Aquí usamos tu SECRET_KEY y ALGORITHM que definimos antes
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Buscar usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.cedula == form_data.username).first()
    
    # 2. Verificar password (aquí usamos passlib)
    if not usuario or not pwd_context.verify(form_data.password, usuario.password_hash):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
    # 3. Crear el token JWT (aquí llamarías a tu función de crear token)
    access_token = create_access_token(data={"sub": usuario.cedula})
    return {"access_token": access_token, "token_type": "bearer"}
'''
# 2. Ruta principal con búsqueda inteligente (Carga Mascotas y Dueños)
@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    nombre: Optional[str] = None, 
    nombre_dueno: Optional[str] = None,
    especie: Optional[str] = None, 
    raza: Optional[str] = None, 
    filtrar_cedula: Optional[str] = None,
    filtrar_apellido: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query_mascotas = db.query(models.Mascota).join(models.Dueno)
    
    if nombre:
        query_mascotas = query_mascotas.filter(models.Mascota.nombre.ilike(f"%{nombre}%"))
    if nombre_dueno:
        query_mascotas = query_mascotas.filter(
            (models.Dueno.nombre.ilike(f"%{nombre_dueno}%")) | 
            (models.Dueno.apellido.ilike(f"%{nombre_dueno}%"))
        )
    if especie:
        query_mascotas = query_mascotas.filter(models.Mascota.especie.ilike(f"%{especie}%"))
    if raza:
        query_mascotas = query_mascotas.filter(models.Mascota.raza.ilike(f"%{raza}%"))
        
    mascotas = query_mascotas.all()

    # CONSULTA BASE DE DUEÑOS 
    query_duenos = db.query(models.Dueno)
    
    if filtrar_cedula and filtrar_cedula.strip():
     query_duenos = query_duenos.filter(models.Dueno.cedula.ilike(f"%{filtrar_cedula.strip()}%"))
    
    if filtrar_apellido and filtrar_apellido.strip():
        query_duenos = query_duenos.filter(models.Dueno.apellido.ilike(f"%{filtrar_apellido.strip()}%"))
    
    duenos = query_duenos.all()

    #  RENDERIZADO DEL TEMPLATE
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "mascotas": mascotas, 
        "duenos": duenos
    })


    

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
# 3. Registrar un Dueño / Cliente Independiente
@app.post("/registrar_dueno/")
def crear_dueno(
    request: Request,
    cedula: str = Form(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    direccion: Optional[str] = Form(None),
    telefono: Optional[str] = Form(None),
    correo: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Validar que no exista otro dueño con la misma cédula
    dueno_repetido = db.query(models.Dueno).filter(models.Dueno.cedula == cedula).first()
    if dueno_repetido:
        mascotas = db.query(models.Mascota).all()
        duenos = db.query(models.Dueno).all()
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "mascotas": mascotas, 
            "duenos": duenos,
            "error_dueno": f"¡Error! Ya existe un dueño registrado con la cédula {cedula}."
        })
    error_msg = None

    if not cedula.isdigit() or len(cedula) != 10:
        error_msg = "La cédula debe contener exactamente 10 dígitos numéricos."
        
    elif not telefono.isdigit():
        error_msg = "El teléfono debe contener únicamente números."
        
    elif correo and not re.match(EMAIL_REGEX, correo):
        error_msg = "El formato del correo electrónico ingresado no es válido."
        
    elif db.query(models.Dueno).filter(models.Dueno.cedula == cedula).first():
        error_msg = f"El cliente con cédula {cedula} ya se encuentra registrado."

    # Si hubo algún error, recargamos la página mostrando la alerta correspondiente
    if error_msg:
        query_mascotas = db.query(models.Mascota).all()
        query_duenos = db.query(models.Dueno).all()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "mascotas": query_mascotas,
            "duenos": query_duenos,
            "error_dueno": error_msg
        })

    # Guardado normal si todo pasa con éxito
    nuevo_dueno = models.Dueno(
        cedula=cedula, nombre=nombre.strip(), apellido=apellido.strip(),
        telefono=telefono, correo=correo,
        direccion=direccion.strip() if direccion else None
    )

  
    db.add(nuevo_dueno)
    db.commit()
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# 4. Registrar una Mascota (Vinculada por ID de dueño)
@app.post("/registrar/")
def crear_mascota(
    request: Request,
    nombre: str = Form(...), 
    especie: str = Form(...), 
    raza: str = Form(...), 
    edad: int = Form(...), 
    dueno_id: int = Form(...),  # Cambiado de nombre_dueno a la llave foránea dueno_id
    db: Session = Depends(get_db)
):
    # Buscar si ya existe una mascota exactamente con los mismos datos clave bajo ese mismo dueño
    mascota_repetida = db.query(models.Mascota).filter(
        models.Mascota.nombre == nombre,
        models.Mascota.especie == especie,
        models.Mascota.raza == raza,
        models.Mascota.edad == edad,
        models.Mascota.dueno_id == dueno_id
    ).first()

    if mascota_repetida:
        mascotas = db.query(models.Mascota).all()
        duenos = db.query(models.Dueno).all()
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "mascotas": mascotas, 
            "duenos": duenos, 
            "error": f"¡Advertencia! La mascota '{nombre}' ya se encuentra registrada con este mismo dueño."
        })

    nueva_mascota = models.Mascota(
        nombre=nombre, especie=especie, raza=raza, edad=edad, dueno_id=dueno_id
    )
    db.add(nueva_mascota)
    db.commit()
    db.refresh(nueva_mascota)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)



# 5. Actualizar mascota
@app.put("/mascota/{mascota_id}")
def actualizar_mascota(
    mascota_id: int, 
    nombre: str = Form(...), 
    especie: str = Form(...), 
    raza: str = Form(...), 
    edad: int = Form(...), 
    dueno_id: int = Form(...), # Cambiado a dueno_id
    observaciones: str = Form(...),  
    db: Session = Depends(get_db)
):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    
    mascota.nombre = nombre
    mascota.especie = especie
    mascota.raza = raza
    mascota.edad = edad
    mascota.dueno_id = dueno_id
    mascota.observaciones = observaciones
    db.commit()
    db.refresh(mascota)
    return {"mensaje": "Mascota actualizada correctamente"}


# 6. Eliminar mascota
@app.delete("/mascota/{mascota_id}")
def eliminar_mascota(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    
    db.delete(mascota)
    db.commit()
    return {"mensaje": "Mascota eliminada de la base de datos"}


# 7. Ver exámenes de una mascota específica
@app.get("/mascota/{mascota_id}/examenes", response_class=HTMLResponse)
def ver_examenes(mascota_id: int, request: Request, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    examenes = db.query(models.Examen).filter(models.Examen.mascota_id == mascota_id).all()
    
    return templates.TemplateResponse("examenes.html", {
        "request": request, 
        "mascota": mascota, 
        "examenes": examenes
    })


# 8. Guardar un nuevo examen (POST)
@app.post("/mascota/{mascota_id}/examen_nuevo")
def registrar_examen(
    mascota_id: int,
    titulo: str = Form(...),
    resultado: str = Form(...),
    db: Session = Depends(get_db)
):
    nuevo_examen = models.Examen(mascota_id=mascota_id, titulo=titulo, resultado=resultado)
    db.add(nuevo_examen)
    db.commit()
    return RedirectResponse(url=f"/mascota/{mascota_id}/examenes", status_code=status.HTTP_303_SEE_OTHER)


# 9. Ver recetas de una mascota específica
@app.get("/mascota/{mascota_id}/recetas", response_class=HTMLResponse)
def ver_recetas(mascota_id: int, request: Request, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return templates.TemplateResponse("recetas.html", {"request": request, "mascota": mascota})


# 10. Guardar una nueva receta (POST)
@app.post("/mascota/{mascota_id}/receta_nueva")
def registrar_receta(mascota_id: int, medicamento: str = Form(...), indicaciones: str = Form(...), db: Session = Depends(get_db)):
    nueva_receta = models.Receta(mascota_id=mascota_id, medicamento=medicamento, indicaciones=indicaciones)
    db.add(nueva_receta)
    db.commit()
    return RedirectResponse(url=f"/mascota/{mascota_id}/recetas", status_code=status.HTTP_303_SEE_OTHER)


# 11. Ver facturas e historial detallado del Dueño
@app.get("/mascota/{mascota_id}/facturas", response_class=HTMLResponse)
def historial_facturas(mascota_id: int, request: Request, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
    facturas = db.query(models.Factura).filter(models.Factura.mascota_id == mascota_id).all()
    
    return templates.TemplateResponse("facturas.html", {
        "request": request, 
        "mascota": mascota, 
        "facturas": facturas
    })


# 12. Guardar una nueva factura (POST)
@app.post("/mascota/{mascota_id}/factura_nueva")
def crear_factura(mascota_id: int, servicio: str = Form(...), monto: float = Form(...), db: Session = Depends(get_db)):
    nueva = models.Factura(mascota_id=mascota_id, servicio=servicio, monto=monto)
    db.add(nueva)
    db.commit()
    return RedirectResponse(url=f"/mascota/{mascota_id}/facturas", status_code=status.HTTP_303_SEE_OTHER)

# 13. Actualizar Dueño / Cliente
@app.put("/dueno/{id}")
def actualizar_dueno(
    id: int,
    cedula: str = Form(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    telefono: str = Form(...),
    correo: Optional[str] = Form(None),
    direccion: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    dueno = db.query(models.Dueno).filter(models.Dueno.id == id).first()
    if not dueno:
        raise HTTPException(status_code=404, detail="Dueño no encontrado")
    
    cedula = cedula.strip()
    telefono = telefono.strip()
    correo = correo.strip() if correo else None

    # Validaciones de formato
    if not cedula.isdigit() or len(cedula) != 10:
        raise HTTPException(status_code=400, detail="La cédula debe contener exactamente 10 dígitos numéricos.")
        
    if not telefono.isdigit():
        raise HTTPException(status_code=400, detail="El teléfono debe contener únicamente números.")
        
    if correo and not re.match(EMAIL_REGEX, correo):
        raise HTTPException(status_code=400, detail="El formato del correo electrónico no es válido.")

    # Validar cédula duplicada en otro ID
    cedula_duplicada = db.query(models.Dueno).filter(models.Dueno.cedula == cedula, models.Dueno.id != id).first()
    if cedula_duplicada:
        raise HTTPException(status_code=400, detail=f"La cédula {cedula} ya pertenece a otro cliente.")

    # Actualización de datos
    dueno.cedula = cedula
    dueno.nombre = nombre.strip()
    dueno.apellido = apellido.strip()
    dueno.telefono = telefono
    dueno.correo = correo
    dueno.direccion = direccion.strip() if direccion else None
    
    db.commit()
    return {"message": "Cliente actualizado con éxito"}

# 14 DESCARGAR HISTORAL DE FACTURAS
@app.get("/mascota/{mascota_id}/facturas/pdf")
def descargar_facturas_pdf(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    facturas = db.query(models.Factura).filter(models.Factura.mascota_id == mascota_id).all()
    contexto = {"request": {}, "mascota": mascota, "facturas": facturas, "current_time": datetime.now().strftime("%Y-%m-%d %H:%M")}
    return generar_pdf_desde_html("facturas_pdf.html", contexto, f"facturas_{mascota.nombre}.pdf")

#15 DESCARGAR FACTURA INDIVIDUAL
@app.get("/factura/{factura_id}/pdf")
def descargar_factura_individual_pdf(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(models.Factura).filter(models.Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    contexto = {"request": {}, "mascota": factura.mascota, "facturas": [factura], "current_time": datetime.now().strftime("%Y-%m-%d %H:%M")}
    return generar_pdf_desde_html("facturas_pdf.html", contexto, f"factura_{factura.id}.pdf")

#16 DESCARGAR EXAMEN INDIVIDUAL
@app.get("/examen/{examen_id}/pdf")
def descargar_examen_individual_pdf(examen_id: int, db: Session = Depends(get_db)):
    examen = db.query(models.Examen).filter(models.Examen.id == examen_id).first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    contexto = {"request": {}, "mascota": examen.mascota, "examenes": [examen], "current_time": datetime.now().strftime("%Y-%m-%d %H:%M")}
    return generar_pdf_desde_html("examenes_pdf.html", contexto, f"examen_{examen.id}.pdf")

#17 DESCARGAR RECETA INDIVIDUAL
@app.get("/receta/{receta_id}/pdf")
def descargar_receta_individual_pdf(receta_id: int, db: Session = Depends(get_db)):
    receta = db.query(models.Receta).filter(models.Receta.id == receta_id).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    contexto = {"request": {}, "mascota": receta.mascota, "recetas": [receta], "current_time": datetime.now().strftime("%Y-%m-%d %H:%M")}
    return generar_pdf_desde_html("recetas_pdf.html", contexto, f"receta_{receta.id}.pdf")

#18 ENVIAR PDF CORREO
@app.post("/enviar-pdf-correo/{mascota_id}")
async def enviar_pdf_correo(mascota_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    
    # 1. Validación: ¿Existe la mascota y tiene dueño con correo?
    if not mascota or not mascota.dueno or not mascota.dueno.correo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="La mascota no existe o el dueño no tiene un correo registrado."
        )
    
    facturas = db.query(models.Factura).filter(models.Factura.mascota_id == mascota_id).all()
    
    pdf_buffer = generar_pdf_buffer("facturas_pdf.html", {
        "mascota": mascota, 
        "facturas": facturas, 
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    # 2. Envío en segundo plano
    background_tasks.add_task(
        enviar_correo_directo, 
        mascota.dueno.correo, 
        f"Reporte - {mascota.nombre}", 
        "Adjunto tu reporte.", 
        pdf_buffer
    )
    
    return {"message": "Correo enviado con éxito"}

#19 descargar examenes pdf
@app.get("/mascota/{mascota_id}/examenes/pdf")
def descargar_examenes_pdf(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    examenes = db.query(models.Examen).filter(models.Examen.mascota_id == mascota_id).all() 
    contexto = {"request": {}, "mascota": mascota, "examenes": examenes, "current_time": datetime.now().strftime("%Y-%m-%d %H:%M")}
    # CORREGIDO: Apuntando a examenes_pdf.html
    return generar_pdf_desde_html("examenes_pdf.html", contexto, f"historial_examenes_{mascota_id}.pdf")

# 20. Descargar historial de recetas (PDF)
@app.get("/mascota/{mascota_id}/recetas/pdf")
def descargar_recetas_pdf(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    recetas = db.query(models.Receta).filter(models.Receta.mascota_id == mascota_id).all()
    
    contexto = {
        "request": {}, 
        "mascota": mascota, 
        "recetas": recetas, 
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    return generar_pdf_desde_html("recetas_pdf.html", contexto, f"historial_recetas_{mascota.nombre}.pdf")

# 21 ELIMINAR FACTURA
@app.post("/factura/{factura_id}/eliminar")
async def eliminar_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(models.Factura).filter(models.Factura.id == factura_id).first()
    
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    mascota_id = factura.mascota_id # Guardamos el ID para redirigir
    
    db.delete(factura)
    db.commit()
    
    return {"message": "Factura eliminada con éxito", "mascota_id": mascota_id}

# 22 ELIMINAR RECETA
@app.post("/receta/{receta_id}/eliminar")
async def eliminar_receta(receta_id: int, db: Session = Depends(get_db)):
    receta = db.query(models.Receta).filter(models.Receta.id == receta_id).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    db.delete(receta)
    db.commit()
    return {"message": "Receta eliminada con éxito"}

# 23 ELIMINAR EXAMEN 
@app.post("/examen/{examen_id}/eliminar")
async def eliminar_examen(examen_id: int, db: Session = Depends(get_db)):
    examen = db.query(models.Examen).filter(models.Examen.id == examen_id).first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    
    db.delete(examen)
    db.commit()
    return {"message": "Examen eliminado con éxito"}

# 24 ELIMINAR DUENO
@app.delete("/dueno/{dueno_id}")
async def eliminar_dueno(dueno_id: int, db: Session = Depends(get_db)):
    # 1. Buscar al dueño
    dueno = db.query(models.Dueno).filter(models.Dueno.id == dueno_id).first()
    
    # 2. Verificar si tiene mascotas
    if dueno.mascotas: 
        raise HTTPException(status_code=400, detail="El cliente tiene mascotas")
        
    db.delete(dueno)
    db.commit()
    return {"message": "Eliminado"}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para registrar (solo la usaría el admin o un registro inicial)
@app.post("/registro")
async def registrar_usuario(cedula: str, password: str, rol: str = "user", db: Session = Depends(get_db)):
    hashed_pw = pwd_context.hash(password)
    nuevo_usuario = models.Usuario(cedula=cedula, password_hash=hashed_pw, rol=rol)
    db.add(nuevo_usuario)
    db.commit()
    return {"message": "Usuario creado exitosamente"}


# Definir la excepción
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
)

SECRET_KEY = "admin" # ¡Cámbiala por una real!
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Esta función obtiene al usuario basándose en el token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        cedula: str = payload.get("sub")
        if cedula is None:
            raise credentials_exception
    except JWTError: # Ahora ya conoce JWTError
        raise credentials_exception
        
    usuario = db.query(models.Usuario).filter(models.Usuario.cedula == cedula).first()
    if usuario is None:
        raise credentials_exception
    return usuario

@app.get("/dashboard")
@app.get("/dashboard")
async def dashboard(
    request: Request, # <-- IMPORTANTE: Agregar esto aquí
    current_user: models.Usuario = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user.rol == "admin":
        return templates.TemplateResponse("panel_admin.html", {"request": request})
    
    return templates.TemplateResponse("cliente.html", {
        "request": request, # <-- Ahora ya existe
        "dueno": current_user.dueno 
    })