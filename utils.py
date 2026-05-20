import io
from fastapi.responses import StreamingResponse
from xhtml2pdf import pisa
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

def generar_pdf_buffer(template_name: str, contexto: dict):
    """
    Renderiza el HTML y retorna el buffer de bytes del PDF.
    Útil para adjuntar en correos o guardar en disco.
    """
    template = templates.get_template(template_name)
    html_content = template.render(contexto)
    
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
    
    if pisa_status.err:
        return None
    
    pdf_buffer.seek(0)
    return pdf_buffer

def generar_pdf_desde_html(template_name: str, contexto: dict, filename: str):
    """
    Función de conveniencia para la descarga directa en navegador.
    """
    pdf_buffer = generar_pdf_buffer(template_name, contexto)
    
    if not pdf_buffer:
        return None
        
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )