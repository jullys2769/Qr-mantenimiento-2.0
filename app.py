from flask import Flask, redirect, send_file
import qrcode
from PIL import Image
import os
from datetime import datetime, timedelta, timezone
import psycopg2

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes

app = Flask(__name__)

# ===============================
# CONFIGURACIÓN
# ===============================

GOOGLE_FORM_URL = "https://forms.gle/YPTJc1tGF3ZJ1gNK9"

# URL pública de Render (cámbiala por la tuya)
PUBLIC_URL = os.environ.get("PUBLIC_URL", "https://TU-APP.onrender.com")

QR_FILE = "qr_maquina.png"
LOGO_FILE = "logo.png"
PDF_FILE = "reporte_qr.pdf"

DATABASE_URL = os.environ.get("DATABASE_URL")

START_DATE = datetime.now() - timedelta(days=1)
DAYS_VALID = 7

# ===============================
# BASE DE DATOS (PostgreSQL)
# ===============================

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def crear_base_datos():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id SERIAL PRIMARY KEY,
            fecha TIMESTAMP,
            estado TEXT
        )
    """)
    conn.commit()
    conn.close()

crear_base_datos()

def guardar_registro(estado):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO registros (fecha, estado) VALUES (%s, %s)",
        (datetime.now(timezone.utc), estado)
    )
    conn.commit()
    conn.close()

# ===============================
# GENERAR QR
# ===============================

def generar_qr():
    url = f"{PUBLIC_URL}/formulario"

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    logo = Image.open(LOGO_FILE)

    qr_width, qr_height = qr_img.size
    logo_size = int(qr_width * 0.25)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
    qr_img.paste(logo, pos, mask=logo if logo.mode == "RGBA" else None)

    qr_img.save(QR_FILE)

if not os.path.exists(QR_FILE):
    generar_qr()

# ===============================
# VALIDACIÓN DE TIEMPO (UTC)
# ===============================

def qr_activo():
    ahora = datetime.now(timezone.utc)
    fecha_expiracion = START_DATE + timedelta(days=DAYS_VALID)
    return START_DATE <= ahora < fecha_expiracion

# ===============================
# GENERAR PDF
# ===============================

def generar_pdf():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, fecha, estado FROM registros ORDER BY id DESC")
    datos = cursor.fetchall()
    conn.close()

    doc = SimpleDocTemplate(PDF_FILE, pagesize=pagesizes.letter)
    elementos = []

    styles = getSampleStyleSheet()
    elementos.append(Paragraph("Reporte de Registros QR", styles["Title"]))
    elementos.append(Spacer(1, 12))

    tabla_datos = [["ID", "Fecha (UTC)", "Estado"]]
    for fila in datos:
        tabla_datos.append([str(fila[0]), str(fila[1]), fila[2]])

    tabla = Table(tabla_datos)
    tabla.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])

    elementos.append(tabla)
    doc.build(elementos)

# ===============================
# RUTAS
# ===============================

@app.route("/")
def home():
    return "Servidor activo 🚀 Usa /qr para ver el QR"

@app.route("/formulario")
def formulario():
    if qr_activo():
        guardar_registro("ACTIVO")
        return redirect(GOOGLE_FORM_URL)
    else:
        guardar_registro("INACTIVO")
        return """
       "<h1>PRUEBA RENDER FUNCIONANDO</h1>"
        """

@app.route("/qr")
def mostrar_qr():
    return send_file(QR_FILE, mimetype="image/png")

@app.route("/reporte")
def descargar_reporte():
    generar_pdf()
    return send_file(PDF_FILE, as_attachment=True)
