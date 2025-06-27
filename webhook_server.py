from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import os

app = Flask(__name__)

def conectar_hoja():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_path = "/etc/secrets/credentials.json" if os.path.exists("/etc/secrets/credentials.json") else "credentials.json"
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    hoja = client.open("Base Clientes QC").worksheet("CLIENTES")
    return hoja

def es_correo_valido(texto):
    return re.match(r"[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+", texto)

def es_direccion(texto):
    return bool(re.search(r"calle|avenida|barrio|colonia|ciudad|manzana|mz|casa|#", texto, re.IGNORECASE))

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

        hoja = conectar_hoja()
        filas = hoja.get_all_records()
        encontrado = False

        telefono_msg = re.sub(r"\D", "", numero)

        for i, fila in enumerate(filas, start=2):
            telefono_hoja = re.sub(r"\D", "", str(fila.get("TELEFONO", "")))
            if telefono_hoja.endswith(telefono_msg[-8:]):
                if es_correo_valido(mensaje):
                    hoja.update_cell(i, 3, mensaje)
                    print(f"✅ Correo actualizado para {fila.get('NOMBRE', 'Desconocido')}")
                elif es_direccion(mensaje):
                    hoja.update_cell(i, 4, mensaje)
                    print(f"✅ Ciudad actualizada para {fila.get('NOMBRE', 'Desconocido')}")
                elif len(mensaje.split()) >= 2:
                    hoja.update_cell(i, 1, mensaje)
                    print(f"✅ Nombre actualizado para número terminado en {telefono_hoja[-4:]}")
                else:
                    print("⚠️ Mensaje no reconocido como dato válido.")
                encontrado = True
                break

        if not encontrado:
            nueva_fila = ["", telefono_msg, "", ""]
            if es_correo_valido(mensaje):
                nueva_fila[2] = mensaje
            elif es_direccion(mensaje):
                nueva_fila[3] = mensaje
            elif len(mensaje.split()) >= 2:
                nueva_fila[0] = mensaje
            hoja.append_row(nueva_fila)
            print("⚠️ Número no encontrado, añadido como nuevo.")

        return "ok", 200

    except Exception as e:
        print("❌ Error procesando webhook:", e)
        return "error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    
