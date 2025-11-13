import tkinter as tk
from tkinter import scrolledtext, messagebox
from main import get_rag_response

class RAGInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Asistente RAG - Evaluación de Respuestas")
        self.root.geometry("600x500")

        # Etiqueta de instrucción
        tk.Label(root, text="Introduce tu pregunta:", font=("Arial", 11)).pack(pady=5)

        # Caja de texto para la pregunta
        self.entry_pregunta = tk.Entry(root, width=80)
        self.entry_pregunta.pack(pady=5)

        # Botón para enviar
        tk.Button(root, text="Enviar", command=self.enviar_pregunta).pack(pady=10)

        # Caja de texto para mostrar respuesta
        tk.Label(root, text="Respuesta:", font=("Arial", 11, "bold")).pack(pady=5)
        self.text_respuesta = scrolledtext.ScrolledText(root, height=8, width=70, wrap="word", state="disabled")
        self.text_respuesta.pack(pady=5)

        # Valoración
        self.frame_valoracion = tk.Frame(root)
        self.frame_valoracion.pack(pady=10)

        tk.Label(self.frame_valoracion, text="¿Te ha gustado la respuesta?", font=("Arial", 10)).grid(row=0, column=0, columnspan=2, pady=5)

        tk.Button(self.frame_valoracion, text="Sí 👍", width=10, command=lambda: self.valorar("Sí")).grid(row=1, column=0, padx=10)
        tk.Button(self.frame_valoracion, text="No 👎", width=10, command=lambda: self.valorar("No")).grid(row=1, column=1, padx=10)

        self.label_feedback = tk.Label(root, text="", font=("Arial", 10))
        self.label_feedback.pack(pady=5)

    def enviar_pregunta(self):
        pregunta = self.entry_pregunta.get().strip()
        if not pregunta:
            messagebox.showwarning("Atención", "Por favor escribe una pregunta.")
            return

        # Limpia campo de respuesta
        self.text_respuesta.config(state="normal")
        self.text_respuesta.delete("1.0", tk.END)
        self.text_respuesta.insert(tk.END, "Generando respuesta...\n")
        self.text_respuesta.config(state="disabled")
        self.root.update()

        try:
            respuesta, contexto = get_rag_response(pregunta)
            print(respuesta)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
            return

        # Mostrar la respuesta
        self.text_respuesta.config(state="normal")
        self.text_respuesta.delete("1.0", tk.END)
        self.text_respuesta.insert(tk.END, respuesta)
        self.text_respuesta.config(state="disabled")

        # Guardar la última pregunta y respuesta para posible logging
        self.ultima_pregunta = pregunta
        self.ultima_respuesta = respuesta

    def valorar(self, valor):
        self.label_feedback.config(text=f"Has valorado esta respuesta con: {valor}")
        # Aquí podrías guardar en un archivo CSV o base de datos
        print(f"[VALORACIÓN] Pregunta: {getattr(self, 'ultima_pregunta', '')}")
        print(f"[VALORACIÓN] Respuesta: {getattr(self, 'ultima_respuesta', '')}")
        print(f"[VALORACIÓN] Resultado: {valor}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = RAGInterface(root)
    root.mainloop()
