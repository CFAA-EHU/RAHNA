from flask import Flask, render_template, request, session, redirect, url_for, jsonify 
from qwen_text import get_rag_response
import os
import csv
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

def leer_historial_session(session_id, max_entries=10):
    archivo = "/data/valoraciones.csv"
    historial = []

    if os.path.exists(archivo):
        with open(archivo, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["session_id"] == session_id:
                    historial.append({
                        "pregunta": row["pregunta"],
                        "respuesta": row["respuesta"],
                        "valoracion": int(row["valoracion"]) if row["valoracion"] else None
                    })

    return historial[-max_entries:]

def guardar_valoracion_csv(session_id, usuario, pregunta, respuesta, valor):
    archivo = "/data/valoraciones.csv"

    # Si no existe, crear encabezado
    archivo_nuevo = not os.path.exists(archivo)

    with open(archivo, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if archivo_nuevo:
            writer.writerow(["session_id", "usuario", "pregunta", "respuesta", "valoracion"])
        writer.writerow([session_id, usuario, pregunta, respuesta, valor])

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    pregunta = data.get("pregunta", "").strip()
    usuario = data.get("usuario", "").strip()

    if not pregunta:
        return jsonify({"error": "Pregunta vacia"}), 400

    if "usuario" not in session and usuario:
        session["usuario"] = usuario

    try:
        thread_id = session["thread_id"]
        respuesta, contexto = get_rag_response(pregunta, thread_id)
    except Exception as e:
        respuesta = f"Error al generar la respuesta: {e}"

    guardar_valoracion_csv(
        session_id = thread_id,
        usuario = session.get("usuario", ""),
        pregunta = pregunta,
        respuesta = respuesta,
        valor = ""
    )

    historial = leer_historial_session(session["thread_id"])

    return jsonify({"respuesta": respuesta, "historial": historial})

@app.route("/", methods=["GET"])
def index():
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())

    return render_template(
        "index.html"
    )

def actualizar_ultima_valoracion(session_id, valor):
    archivo = "/data/valoraciones.csv"
    filas = []

    with open(archivo, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        filas = list(reader)

    for i in range(len(filas) - 1, 0, -1):
        if filas[i][0] == session_id and filas[i][4] == "":
            filas[i][4] = str(valor)
            break

    with open(archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(filas)

@app.route("/valorar/<int:valor>")
def valorar(valor):
    if valor < 0 or valor > 5:
        return redirect(url_for("index"))

    actualizar_ultima_valoracion(session["thread_id"], valor)

    historial = leer_historial_session(session["thread_id"])

    return jsonify({"historial": historial})

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=8080)
