# ProyectoFrameworks_VeterinariaFastAPI
Proyecto para la materia Programación usando Frameworks

# TEMA:  Sistema de Gestión Clínica Veterinaria 🚀
Esta plataforma web permite la administración integral de clínicas veterinarias, optimizando el control de pacientes (mascotas), la gestión de propietarios, el historial clínico, exámenes, recetas y la facturación automatizada. El sistema resuelve la desorganización en el manejo de registros físicos, permitiendo una atención más eficiente y digitalizada.

# 📋 Características
Gestión de Clientes y Pacientes: Registro, edición y eliminación de propietarios y sus mascotas vinculadas, con validación de integridad referencial.

Historial Médico Digital: Registro y consulta de exámenes médicos y recetas, con capacidad de exportación a PDF para mayor accesibilidad.

Sistema de Facturación: Generación automática de facturas personalizadas por servicios, con envío directo al correo electrónico del cliente.

Seguridad y Control: Implementación de autenticación segura, manejo de sesiones y control de acceso basado en roles (Admin/Consulta).

Integración de Servicios: Envío de notificaciones y documentos mediante servicios SMTP (Mailtrap/Email).

# 🛠️ Requisitos
Para ejecutar este proyecto, necesitas tener instalado Python 3.10 o superior y las siguientes librerías:

fastapi

uvicorn

sqlalchemy

jinja2

python-multipart

passlib[bcrypt]

aiosmtplib (para el envío de correos)

Puedes instalar las dependencias con:
pip install -r requirements.txt

# ⚙️ Instalación
Instrucciones paso a paso para poner en marcha el entorno de desarrollo:

Clona el repositorio:
git clone https://github.com/tu-usuario/nombre-del-repo.git

Instala las dependencias:
pip install -r requirements.txt

Ejecuta la aplicación:
uvicorn main:app --reload

Accede en tu navegador a: http://127.0.0.1:8000

# 🚀 Uso
Una vez iniciada la aplicación, el sistema solicitará credenciales de acceso. Como Administrador, tendrás acceso total a:

Registrar nuevos clientes.

Emitir facturas y enviar documentos por correo electrónico.

Gestionar el historial médico.

Como Usuario de consulta, podrás visualizar el historial de pacientes sin capacidad de modificar registros, garantizando la seguridad de la información.

# 🤝 Contribuir
Si deseas colaborar en la mejora del sistema:

Haz un fork del repositorio.

Crea una nueva rama para tu funcionalidad (git checkout -b feature/nueva-funcionalidad).

Realiza tus cambios y haz commit (git commit -m 'Agregar nueva funcionalidad').

Abre un Pull Request para revisión.

# 📄 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

⌨️ con ❤️ por [Tu Nombre] 😊
