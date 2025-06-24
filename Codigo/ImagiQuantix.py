import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import cv2
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from ObtenerPuntos import ObtenerPuntos
import os
import sys
import time
import numpy as np

def recurso_path(nombre_archivo):
    if getattr(sys, 'frozen', False):
        # Ejecutable (.exe)
        base_path = os.path.join(sys._MEIPASS, "Fondo")
    else:
        # Modo desarrollo (desde .py)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Fondo'))
    return os.path.join(base_path, nombre_archivo)
class ImagiQuantix:
    def __init__(self, master):
        self.master = master
        self.master.title("ImagiQuantix")
        self.master.geometry("1200x800")

        self.ruta_imagen = None
        self.resultados = None
        self.procesador = None
        #Inicialmente el slider no existe
        self.slider_umbral = None 

        self.ultima_actualizacion = time.time()
        self.actualizacion_pendiente = None
        self.eje_y = []
        self.eje_x = []
        

        # Crear un Canvas para manejar el fondo de pantalla y el resto de elementos
        self.canvas = tk.Canvas(self.master, width=1200, height=800, bg="#5D3A9B")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Cargar la imagen de fondo
        self.fondo_original = Image.open(recurso_path("Fondo.jpg"))  # Ruta de la nueva imagen
        self.redimensionar_fondo()
        
        # Crear marco principal encima del canvas
        self.main_frame = tk.Frame(self.canvas, bg="#572364", bd=2, relief=tk.RIDGE)
        self.main_frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
    
        # Redimensionar el fondo al cambiar el tamaño de la ventana
        self.master.bind("<Configure>", self.redimensionar)
        
        # Lado izquierdo: Se encuentra la imagen que vamos a importar
        self.izquierda_frame = tk.Frame(self.main_frame, width=600, bg="white", relief=tk.RIDGE, bd=2)
        self.izquierda_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Etiqueta que contiene el titulo para mostrar el nombre de la imagen
        self.label_titulo_imagen = tk.Label(self.izquierda_frame, text="", font=("Arial", 15, "bold"), fg="#3B1B43",bg="white")
        self.label_titulo_imagen.pack(pady=5)

        # Lado derecho: Se encuentra el panel de controles con las coordenadas y los botones
        self.derecha_frame = tk.Frame(self.main_frame, width=600, bg="white", bd=1)
        self.derecha_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        #Recuadro para la imagen
        self.figura = plt.Figure(figsize=(6, 6))
        self.ax = self.figura.add_subplot(111)
        self.ax.axis("off")
        self.canvas_fig = FigureCanvasTkAgg(self.figura, master=self.izquierda_frame)
        self.canvas_widget = self.canvas_fig.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        #Etiqueta para total de puntos
        self.label_eje_y = tk.Label(self.izquierda_frame, text="", font=("Arial", 15, "bold"), fg="#3B1B43", bg="white")
        self.label_eje_y.pack(pady=10)

        #Título de las coordenadas
        self.label_coordenadas = tk.Label(self.derecha_frame, text="Coordenadas Detectadas:", font=("Arial", 15, "bold"), fg="#3B1B43" ,bg="white")
        self.label_coordenadas.pack(pady=10)

        #Recuadro de texto para las coordenadas
        self.text_area = ScrolledText(self.derecha_frame, width=80, height=30, state=tk.DISABLED, bg="white", fg="black", relief=tk.RIDGE, bd=2)
        self.text_area.pack(pady=10, fill=tk.BOTH, expand=True)

        #Botones
        self.button_frame = tk.Frame(self.derecha_frame, bg="white")
        self.button_frame.pack(pady=10)

        #Estilo de botones
        button_style = {
            "bg": "#3B1B43",
            "fg": "white",
            "relief": "raised",
            "bd": 4,
            "font": ("Arial", 12, "bold"),
            "highlightbackground": "#E5CFF7",
            "highlightthickness": 2
        }

        #Botón subir imagen
        self.btn_subir = tk.Button(self.button_frame, text="Subir Imagen", command=self.cargar_imagen, **button_style)
        self.btn_subir.pack(side=tk.LEFT, padx=5)

        #Botón obtener coordenadas
        self.btn_coordenadas = tk.Button(self.button_frame, text="Obtener Coordenadas", state=tk.DISABLED, command=self.obtener_coordenadas, **button_style)
        self.btn_coordenadas.pack(side=tk.LEFT, padx=5)

        #Botón exportar coordenadas
        self.btn_exportar = tk.Button(self.button_frame, text="Exportar Coordenadas", state=tk.DISABLED, command=self.exportar_coordenadas, **button_style)
        self.btn_exportar.pack(side=tk.LEFT, padx=5)

        #Botón de gráfica
        self.btn_grafica = tk.Button(self.button_frame, text="Gráfica", state=tk.DISABLED, command=self.mostrar_grafica, **button_style)
        self.btn_grafica.pack(side=tk.LEFT, padx=5)  # Mismo estilo y alineación

        #Barra de estado
        self.status_bar = tk.Label(master, text="Esperando acción del usuario...", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="white")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        #Desactivar slider
        self.desactivar_slider()

        #Cierra ventana 
        self.master.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

    #Redimensionar la imagen de fondo al tamaño de la ventana y aplica de forma inmediata
    def redimensionar_fondo(self):
        width = self.master.winfo_width() or 1200
        height = self.master.winfo_height() or 800
        redimensionar_imagen = self.fondo_original.resize((width, height), Image.LANCZOS)
        self.imagen_fondo = ImageTk.PhotoImage(redimensionar_imagen)
        #Si ya existe la imagen solo la actualizo
        if hasattr(self,'background'):
            self.canvas.itemconfig(self.background, image=self.imagen_fondo)
        else:
            self.background = self.canvas.create_image(0,0, image=self.imagen_fondo, anchor = tk.NW)
    
    #Se ejecuta cuando cambia el tamaño de la ventana para actualizar el fondo
    def redimensionar(self, event):
        self.redimensionar_fondo()
    
    #Crea y muestra el slider con los botones para aumentar y disminuir el valor
    def mostrar_slider(self):
        if not hasattr(self, "slider_frame"):
            #Contenedor del slider y botones
            self.slider_frame = tk.Frame(self.derecha_frame, bg="white")

            #Botón para disminuir el valor
            self.btn_menos = tk.Button(self.slider_frame, text="-", font=("Arial", 12, "bold"), width=3, command=self.disminuir_slider, state=tk.DISABLED, bg="#3B1B43", fg="white")
            self.btn_menos.pack(side=tk.LEFT, padx=5)

            #Slider
            self.slider_umbral = tk.Scale(
                self.slider_frame, from_=1, to=50, orient=tk.HORIZONTAL,
                label="", length=400, command=self.programar_actualizacion,
                state=tk.DISABLED,  # Inicialmente deshabilitado
                bg="#3B1B43",
                fg= "white",
                highlightbackground="black",
                highlightthickness=2,
                highlightcolor="black"
            )
            #Inicia en 1
            self.slider_umbral.set(1)
            self.slider_umbral.pack(side=tk.LEFT, padx=5)

            #Botón para aumentar el valor
            self.btn_mas = tk.Button(self.slider_frame, text="+", font=("Arial", 12, "bold"), width=3, command=self.aumentar_slider, state=tk.DISABLED, bg="#3B1B43", fg="white")
            self.btn_mas.pack(side=tk.LEFT, padx=5)

            #Mostrar el slider y los botones
            self.slider_frame.pack(pady=5)

    #Habilita el slider y los botones después de presionar el botón "Obtener coordenadas"
    def habilitar_slider(self):
        self.slider_umbral.config(state=tk.NORMAL)
        self.slider_umbral.config(command=self.programar_actualizacion)
        self.btn_menos.config(state=tk.NORMAL)
        self.btn_mas.config(state=tk.NORMAL)   
        self.slider_frame.pack(pady=5)
    
    #Desactiva el sider y los botones de más y menos al no tener imagen o al subir una imagen nueva 
    def desactivar_slider(self):
       if self.slider_umbral:
        self.slider_umbral.set(1)
        self.slider_umbral.config(state=tk.DISABLED)
        self.btn_menos.config(state=tk.DISABLED)
        self.btn_mas.config(state=tk.DISABLED)

        self.slider_umbral.config(command="")
        self.slider_frame.pack_forget()

    #Disminuye el valor del slider en 1 
    def disminuir_slider(self):
        valor_actual = self.slider_umbral.get()
        #Evita valores menores a 1
        if valor_actual > 1: 
            self.slider_umbral.set(valor_actual - 1)
            self.programar_actualizacion(valor_actual - 1)

    #Aumenta el valor del slider en 1 
    def aumentar_slider(self):
        """Aumenta el valor del slider en 1 unidad."""
        valor_actual = self.slider_umbral.get()
        #Evita valores mayores a 50
        if valor_actual < 50:  
            self.slider_umbral.set(valor_actual + 1)
            self.programar_actualizacion(valor_actual + 1)

    #Programa la actualización del umbral de detección para mejorar la fluidez
    def programar_actualizacion(self, valor):
        #Evita múltiples actualizaciones seguidas
        if self.actualizacion_pendiente:
            return  
        self.actualizacion_pendiente = True
        self.master.after(50, lambda: self.actualizar_deteccion_async(valor))

    #Actualiza la detección de forma más fluida
    def actualizar_deteccion_async(self, valor):
        self.actualizacion_pendiente = False
        self.actualizar_deteccion(valor)
    
    #Actualizar detección de puntos 
    def actualizar_deteccion(self, valor):
        if not self.ruta_imagen:
            return
        
        try:
            #Convertir el valor del slider a entero
            umbral = int(valor)
            self.status_bar.config(text=f"Ajustando umbral: {umbral}")
            
            #Verificar si la imagen se ha cargado antes de procesar 
            if self.imagen_original is None:
                messagebox.showerror("Error", "La imagen no se ha cargado ninguna imagen.")
                return

            # Volver a procesar la imagen con el nuevo umbral
            self.procesador = ObtenerPuntos(self.ruta_imagen, dimension_bloque=100, distancia_minima=umbral)
            self.procesador.suavizar_y_quitar_ruido()
            self.procesador.procesar_imagen()
            
            self.resultados = sorted(self.procesador.info_bloque, key=lambda p: (p['fila'], p['columna']))
            
            #Mostrar la imagen actualizada
            salida = cv2.cvtColor(self.procesador.imagen, cv2.COLOR_GRAY2BGR)
            for punto in self.resultados:
                x, y, r, intensidad = punto["x"], punto["y"], punto["r"], punto["intensidad"]
                if intensidad > 128:
                    color = (0, 0, 255)  
                else:
                    color = (255, 0, 255)
                cv2.circle(salida, (x, y), r, color, 6)
                cv2.circle(salida, (x, y), 2, (0, 255, 255), 3)

            self.ax.clear()
            self.ax.imshow(cv2.cvtColor(salida, cv2.COLOR_BGR2RGB))
            self.ax.axis("off")
            self.canvas_fig.draw()
            
            #Actualizar la matriz de coordenadas
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "| Punto | Bloque | Fila | Columna | Intensidad | Eje X | Eje Y | Diámetro |\n")
            self.text_area.insert(tk.END, "+-------+--------+------+---------+------------+-------+-------+----------+\n")

            for i, punto in enumerate(self.resultados, start=1):
                self.text_area.insert(tk.END, f"| {i:<5} | {punto['bloque']:<6} | {punto['fila']:<4} | {punto['columna']:<7} | {punto['intensidad']:<10} | {punto['x']:<5} | {punto['y']:<5} | {punto['diametro']:<8} |\n")

            self.text_area.insert(tk.END, "+-------+--------+------+---------+------------+-------+-------+----------+\n")
            self.text_area.config(state=tk.DISABLED)
            self.label_eje_y.config(text=f"Total de puntos encontrados: {len(self.resultados)}")
            self.eje_y.append(len(self.resultados)) #Puntos detectados
            umbral_actual = self.slider_umbral.get()
            self.eje_x.append(umbral_actual)
            self.status_bar.config(text="Umbral ajustado con éxito.")

        except Exception as e:
            self.status_bar.config(text="Error al actualizar la detección.")
            messagebox.showerror("Error", f"Error al actualizar la detección: {e}")

    #Muestra la gráfica, siendo el eje_x el valor del umbral(slider) cada vez que suelta y el eje_y el número total de puntos
    def mostrar_grafica(self):
        ventana_grafica = Toplevel(self.master)
        ventana_grafica.title("Gráfica de Puntos Detectados")
        fig, ax = plt.subplots(figsize=(12,10))
        
        x_values = self.eje_x 
        y_values = self.eje_y
        ax.plot(x_values, y_values, marker='o', linestyle='-')
        
        #Añadir texto con el número de puntos al lado de cada punto
        for i, txt in enumerate(y_values):
            ax.text(x_values[i], y_values[i], str(txt), fontsize=12, verticalalignment='bottom', horizontalalignment='right')

        ax.set_xlabel("Umbral (Slider)")
        ax.set_ylabel("Total de Puntos")
        ax.set_title("Gráfica de Puntos Detectados")
        canvas = FigureCanvasTkAgg(fig, master=ventana_grafica)
        canvas.get_tk_widget().pack()
        canvas.draw()

    #Carga la imagen a la interfaz
    def cargar_imagen(self):
        self.ruta_imagen = filedialog.askopenfilename(filetypes=[("Imágenes TIFF", "*.tif"), ("Todas", "*.*")])
        
        if not self.ruta_imagen:
            messagebox.showwarning("Advertencia", "No se seleccionó ninguna imagen.")
            return
        
        try:
            self.status_bar.config(text="Cargando imagen...")

            #Verificar si la imagen es válida
            try:
                with Image.open(self.ruta_imagen) as img:
                    img.verify()
            except Exception as e:
                messagebox.showerror("Error", f"La imagen selecionada no es válida:{e}")
                return
            
            # Verificar si OpenCV puede cargar la imagen
            self.imagen_original = cv2.imread(self.ruta_imagen, cv2.IMREAD_GRAYSCALE)
            if self.imagen_original is None:
                raise ValueError("La imagen no se pudo cargar. Verifique el formato o la ruta.")

            self.imagen_mostrar = self.imagen_original.copy()
            # Limpiar la sección de coordenadas detectadas
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete(1.0, tk.END) 
            self.text_area.config(state=tk.DISABLED)
            self.btn_exportar.config(state=tk.DISABLED)
            self.btn_grafica.config(state=tk.DISABLED)
            self.desactivar_slider()
            self.actualizacion_pendiente = False
            
            #Actualiza la etiqueta de total de puntos
            self.label_eje_y.config(text="Total de puntos encontrados: 0")
            self.eje_y.clear()
            self.eje_x.clear() 
            self.procesador = None
            self.resultados = None
           
            #Actualiza título con el nombre de la imagen
            nombre_imagen = os.path.basename(self.ruta_imagen)
            self.label_titulo_imagen.config(text=nombre_imagen)

            # Mostrar nueva imagen en el frame
            self.ax.clear()
            self.ax.imshow(self.imagen_mostrar, cmap="gray")
            self.ax.axis("off")
            self.canvas_fig.draw()

            #Habilitar botón para obtener coordenadas
            self.btn_coordenadas.config(state=tk.NORMAL)
           
            #Mostrar el slider después de cargar la imagen
            self.slider_umbral.pack(pady=5)  
            self.status_bar.config(text="Imagen cargada con éxito.")

        except Exception as e:
            self.status_bar.config(text="Error al cargar la imagen.")
            
    #Obtiene las coordenadas de los puntos 
    def obtener_coordenadas(self):
        try:
            self.status_bar.config(text="Procesando imagen para obtener coordenadas...")

            if not self.ruta_imagen:
                raise ValueError("No se ha cargado ninuna imagen.")
           
            procesador = ObtenerPuntos(self.ruta_imagen, dimension_bloque=100, distancia_minima=20)
            procesador.suavizar_y_quitar_ruido()
            procesador.procesar_imagen()
            
            self.resultados = sorted(procesador.info_bloque, key=lambda p: (p['fila'], p['columna']))

            salida = cv2.cvtColor(procesador.imagen, cv2.COLOR_GRAY2BGR)
            for punto in self.resultados:
                x, y, r, intensidad = punto["x"], punto["y"], punto["r"], punto["intensidad"]
                if intensidad > 128:
                    color = (0, 0, 255)  
                else:
                    color = (255, 0, 255)
                cv2.circle(salida, (x, y), r, color, 6)
                cv2.circle(salida, (x, y), 2, (0, 255, 255), 3)

            self.ax.clear()
            self.ax.imshow(cv2.cvtColor(salida, cv2.COLOR_BGR2RGB))
            self.ax.axis("off")
            self.canvas_fig.draw()

            #Mostrar el slider cuando se hayan obtenido las coordenadas
            self.mostrar_slider() 
            self.habilitar_slider()
            self.btn_grafica.config(state=tk.NORMAL)
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete(1.0, tk.END)

            #Encabezado
            self.text_area.insert(tk.END, "| Punto | Bloque | Fila | Columna | Intensidad  | Eje X | Eje Y | Diámetro |\n")
            self.text_area.insert(tk.END, "+-------+--------+------+---------+-------------+-------+-------+----------+\n")

            #Datos
            for i, punto in enumerate(self.resultados, start=1):
                self.text_area.insert(tk.END, f"| {i:<5} | {punto['bloque']:<6} | {punto['fila']:<4} | {punto['columna']:<7} | {punto['intensidad']:<11} | {punto['x']:<5} | {punto['y']:<5} | {punto['diametro']:<8} |\n")

            self.text_area.insert(tk.END, "+-------+--------+------+---------+-------------+-------+-------+----------+\n")
            self.text_area.config(state=tk.DISABLED)
            self.label_eje_y.config(text=f"Total de puntos encontrados: {len(self.resultados)}")
            self.btn_exportar.config(state=tk.NORMAL)
            self.status_bar.config(text="Procesamiento completado con éxito.")
        except Exception as e:
            self.status_bar.config(text="Error durante el procesamiento.")
            messagebox.showerror("Error", f"Error al procesar la imagen: {e}")
        finally:
            pass  

    #Exporta las coordenadas a un fichero .txt
    def exportar_coordenadas(self):
        try:
            if not self.resultados:
                raise ValueError("No hay resultados para exportar.")

            nombre_archivo = os.path.splitext(os.path.basename(self.ruta_imagen))[0] + "_coordenadas.txt"
            ruta_guardado = filedialog.asksaveasfilename(initialfile=nombre_archivo, defaultextension=".txt", filetypes=[("Archivo de texto", "*.txt")])
            if not ruta_guardado:
                return
            with open(ruta_guardado, "w") as archivo:
                archivo.write(f"Nombre de la imagen: {os.path.basename(self.ruta_imagen)}\n")
                archivo.write("| Punto | Bloque | Fila | Columna | Intensidad  | Eje X | Eje Y | Diámetro |\n")
                archivo.write("+-------+--------+------+---------+-------------+-------+-------+----------+\n")
                for i, punto in enumerate(self.resultados, start=1):
                    archivo.write(f"| {i:<5} | {punto['bloque']:<6} | {punto['fila']:<4} | {punto['columna']:<7} | {punto['intensidad']:<11} | {punto['x']:<5} | {punto['y']:<5} | {punto['diametro']:<8} |\n")
                archivo.write("+-------+--------+------+---------+-------------+-------+-------+----------+\n")

            self.status_bar.config(text="Coordenadas exportadas con éxito.")
            messagebox.showinfo("Éxito", "Coordenadas exportadas correctamente.")
        except Exception as e:
            self.status_bar.config(text="Error al exportar coordenadas.")
            messagebox.showerror("Error", f"Error al exportar las coordenadas: {e}")
    
    #Detiene todo los procesos y cierra la aplicación correctamente
    def cerrar_aplicacion(self):
        self.master.quit()  
        self.master.destroy() 


if __name__ == "__main__":
    root = tk.Tk()
    app = ImagiQuantix(root)
    root.mainloop() 