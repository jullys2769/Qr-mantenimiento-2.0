from flask import Flask, redirect, send_file
import qrcode
from PIL import Image
import os
from datetime import datetime, timedelta
import sqlite3

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
SERVER_IP = "192.168.100.197"
PORT = 5000

QR_FILE = "qr_maquina.png"
LOGO_FILE = "logo.png"
PDF_FILE = "reporte_qr.pdf"
DB_FILE = "registros.db"

START_DATE = datetime(2026, 2, 17)
DAYS_VALID = 7

# ===============================
# BASE DE DATOS
# ===============================

def crear_base_datos():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            estado TEXT
        )
    """)

    conn.commit()
    conn.close()

crear_base_datos()

def guardar_registro(estado):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("INSERT INTO registros (fecha, estado) VALUES (?, ?)",
                   (fecha, estado))

    conn.commit()
    conn.close()

# ===============================
# GENERAR QR
# ===============================

def generar_qr():
    url = f"http://{SERVER_IP}:{PORT}/formulario"

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

    pos = ((qr_width - logo_size) // 2,
           (qr_height - logo_size) // 2)

    qr_img.paste(logo, pos, mask=logo if logo.mode == "RGBA" else None)

    qr_img.save(QR_FILE)

if not os.path.exists(QR_FILE):
    generar_qr()

# ===============================
# VALIDACIÓN DE TIEMPO
# ===============================

def qr_activo():
    hoy = datetime.now()
    fecha_expiracion = START_DATE + timedelta(days=DAYS_VALID)
    return START_DATE <= hoy < fecha_expiracion

# ===============================
# GENERAR PDF
# ===============================

def generar_pdf():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registros")
    datos = cursor.fetchall()
    conn.close()

    doc = SimpleDocTemplate(PDF_FILE, pagesize=pagesizes.letter)
    elementos = []

    styles = getSampleStyleSheet()
    elementos.append(Paragraph("Reporte de Registros QR", styles["Title"]))
    elementos.append(Spacer(1, 12))

    tabla_datos = [["ID", "Fecha", "Estado"]]

    for fila in datos:
        tabla_datos.append(list(fila))

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

@app.route("/formulario")
def formulario():
    if qr_activo():
        guardar_registro("ACTIVO")
        return redirect(GOOGLE_FORM_URL)
    else:
        guardar_registro("INACTIVO")
        return """
        <h1>⛔ QR deshabilitado</h1>
        <p>Mantenimiento realizado.</p>
        """

@app.route("/qr")
def mostrar_qr():
    return send_file(QR_FILE, mimetype="image/png")

@app.route("/reporte")
def descargar_reporte():
    try:
        generar_pdf()
        return send_file(PDF_FILE, as_attachment=True)
    except Exception as e:
        return f"Error al generar/descargar PDF: {e}"

# ===============================
# INICIAR SERVIDOR
# ===============================

import threading

from flask import Flask

app = Flask(__name__)

# tus rutas
@app.route("/")
def home():
    return "OK"

def iniciar_servidor():
    app.run(host="127.0.0.1", port=PORT, debug=False)

#if __name__ == "__main__":
    #hilo = threading.Thread(target=iniciar_servidor)
    #hilo.daemon = True
    #hilo.start()

    webview.create_window("Sistema Control QR", f"http://127.0.0.1:{PORT}")
    webview.start()