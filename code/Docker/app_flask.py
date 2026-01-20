from flask import Flask, render_template, request, session, redirect, url_for 
from qwen_text import get_rag_response
import os
import csv
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route("/", methods=["GET", "POST"])
def index():
    respuesta = None

    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())

    if "historial" not in session:
        session["historial"] = []

    if request.method == "POST":
        session.pop("feedback", None)

        pregunta = request.form.get("pregunta", "").strip()

        if "usuario" not in session:
            session["usuario"] = request.form.get("usuario")

        if pregunta:
            try:
                thread_id = session["thread_id"]
                respuesta, contexto = get_rag_response(pregunta, thread_id)
            except Exception as e:
                respuesta = f"Error al generar respuesta: {e}"

            # Guardamos en sesión para poder valorarlo luego
            session["ultima_pregunta"] = pregunta
            session["ultima_respuesta"] = respuesta

            # Añadir al historial
            session["historial"].append({
                "pregunta": pregunta,
                "respuesta": respuesta,
                "valoracion": None
            })

            session.modified = True  # importante

    respuesta_pendiente = False
    if session.get("historial"):
        if session["historial"][-1]["valoracion"] is None:
            respuesta_pendiente = True

    return render_template(
        "index.html",
        respuesta=respuesta,
        historial=session.get("historial", []),
        respuesta_pendiente=respuesta_pendiente
    )

def guardar_valoracion_csv(usuario, pregunta, respuesta, valor):
    archivo = "/data/valoraciones.csv"

    # Si no existe, crear encabezado
    archivo_nuevo = not os.path.exists(archivo)

    with open(archivo, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if archivo_nuevo:
            writer.writerow(["usuario", "pregunta", "respuesta", "valoracion"])
        writer.writerow([usuario, pregunta, respuesta, valor])

@app.route("/valorar/<int:valor>")
def valorar(valor):
    if valor < 0 or valor > 5:
        return redirect(url_for("index"))

    usuario = session.get("usuario", "")

    if "historial" in session and session["historial"]:
        # Actualizar la última entrada
        session["historial"][-1]["valoracion"] = valor
        session.modified = True

        pregunta = session["historial"][-1]["pregunta"]
        respuesta = session["historial"][-1]["respuesta"]

        guardar_valoracion_csv(usuario, pregunta, respuesta, valor)

        session["feedback"] = f"<strong>Pregunta:</strong> {pregunta}.\n <strong>Respuesta:</strong> {respuesta}.\n Has valorado esta respuesta con: <strong>{valor}/5</strong>"

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=8080)
