from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

app = Flask(__name__)

def conectar_hoja():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    hoja = client.open("Base Clientes QC").sheet1
    return hoja

def es_correo_valido(texto):
    return re.match(r"[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+", texto)

@app.route("/", methods=["GET"])
def home():
    return "Servidor webhook activo para Quick Cargo Nicaragua."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        datos = request.form
        numero = datos.get("From", "")
        mensaje = datos.get("Body", "").strip()

        print(f"📩 Mensaje recibido de {numero}: {mensaje}")

        if es_correo_valido(mensaje):
            hoja = conectar_hoja()
            filas = hoja.get_all_records()
            encontrado = False

            for i, fila in enumerate(filas, start=2):  # empieza desde fila 2 por encabezados
                if str(fila.get("TELEFONO", "")).endswith(numero[-8:]):
                    hoja.update_cell(i, 3, mensaje)  # columna 3 = columna C = CORREO
                    print(f"✅ Correo actualizado para {fila.get('NOMBRE', 'Desconocido')}")
                    encontrado = True
                    break

            if not encontrado:
                hoja.append_row(["Desconocido", numero, mensaje, "Ciudad no definida"])
                print("⚠️ Número no encontrado, añadido como nuevo.")

        return "ok", 200

    except Exception as e:
        print("❌ Error procesando webhook:", e)
        return "error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
