import cv2
import matplotlib.pyplot as plot
import numpy as np

class ObtenerPuntos:
    def __init__(self, ruta_imagen, dimension_bloque = 100, distancia_minima = 15, roi = None): #La dimensión bloque es un parámetro que define el tamaño de cada bloque en píxeles, en este caso se divide la imagen en bloques de tamaño 100x100 pixeles 
        #Inicialización de parámetros
        self.ruta_imagen = ruta_imagen
        self.imagen = self.cargar_imagen()
        self.dimension_bloque = dimension_bloque
        self.distancia_minima = distancia_minima
        #Lista para almacenar la información de cada punto detectado
        self.info_bloque = [] 
        #Calculo de filas y columnas dinámicamente
        self.num_filas, self.num_columnas = self.cuadricula()   
        #Región de interés
        self.roi = roi 
        #Almacena la imagen procesada
        self.imagen_procesada = None 
    
    #Función para cargar la imagen TIFF en escala de grises
    def cargar_imagen(self):
        imagen = cv2.imread(self.ruta_imagen, cv2.IMREAD_GRAYSCALE)
        if imagen is None:
            raise ValueError (f"No se pudo cargar la imagen desde {self.ruta_imagen}")
        return imagen

    #Función para dividir la imagen en bloques y devuelve el número de filas y columnas
    def cuadricula (self):
        altura, ancho = self.imagen.shape
        num_filas = altura // self.dimension_bloque 
        num_columnas = ancho // self.dimension_bloque
        return num_filas, num_columnas
    
    #Función para suavizar y quitar ruido de la imagen
    def suavizar_y_quitar_ruido(self):
        #Aplica un filtro bilateral para suavizar y preservar bordes
        imagen_suavizada = cv2.bilateralFilter(self.imagen, d=5, sigmaColor=75, sigmaSpace=75)
        
        #Operación de cierre para eliminar manchas alargadas
        kernel_cierre = cv2.getStructuringElement(cv2.MORPH_RECT,(9,9))
        imagen_cierre = cv2.morphologyEx(imagen_suavizada, cv2.MORPH_CLOSE,kernel_cierre, iterations=3)

        #Operación de apertura para eliminar pequeños puntos sueltos
        kernel_abrir = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9))
        imagen_limpia = cv2.morphologyEx(imagen_cierre, cv2.MORPH_OPEN, kernel_abrir,iterations=2)
        
        #Actualiza la imagen 
        self.imagen = imagen_limpia

    #Función para procesar la imagen
    def procesar_imagen (self):
        # Aplizar suavizado o desenfoque gaussiano para reducir el ruido antes de la detección de círculos en la imagen 
        imagen_suavizada = cv2.GaussianBlur(self.imagen, (5, 5), 1)
        
        #Detección de circulos utilizando HoughCircles
        circulos = cv2.HoughCircles(
            imagen_suavizada,
            cv2.HOUGH_GRADIENT_ALT, 
            dp=0.3, #Resolución acumulador 
            minDist= 20, #Distancia mínima entre centros
            param1=40, #Primer umbral para el detector de bordes Canny
            param2= 0.1,  #Umbral del acumulador (sensibilidad de detección)
            minRadius=1, #Radio mínimo de los círculos
            maxRadius=25  #Radio máximo de los círculos
        )
        #Si se detectan círculos, se rodean sus coordenadas.
        #Asegurar que al menos se hayan encontrado algunos círculos
        if circulos is not None:
            circulos = np.round(circulos[0, :]).astype("int")
            print(f"Número de {len(circulos)} circulos encontrados aproximadamente")
            #Filtrar tanto los cercanos como los superpuestos
            circulos = self.filtrar_circulos(circulos)

            #Dibujar los círculos detectados en la imagen y convierte la imagen en BGR (escala de grises) 
            salida = cv2.cvtColor(self.imagen, cv2.COLOR_GRAY2BGR)

            #Iterar sobre los círculos y obtener la intensidad de los mismos en la imagen    
            for (x, y, r) in circulos:
                intensidad = self.imagen[y,x]
                if intensidad > 128: # Rojo para alta intensidad
                    color = (0, 0, 255) 
                    grosor = 6 
                else: 
                    color = (255, 0, 255) # Rosa para baja intensidad
                    grosor = 6

                cv2.circle(salida, (x, y), r, color, grosor) 
                cv2.circle(salida, (x, y), 2,(0,255,255), 3) #Centro del circulo
                self.calcular_info_bloque(x,y,r,intensidad)
            
                #Almacena la imagen procesada con los círculos dibujados
                self.imagen_procesada = salida

           # Mostrar la imagen con los círculos detectados
           # plot.imshow(cv2.cvtColor(salida, cv2.COLOR_BGR2RGB))
           # plot.title("Circulos Detectados", color = "black")
           # plot.axis("off")
           # plot.show()   
        else:
            print("No se ha encontrado ningún circulo")
            self.imagen_procesada = self.imagen
    
    #Función que filtra los círculos que se encuentran cerca entre sí o fuera del ROI
    def filtrar_circulos(self, circulos):
        filtrados =[]
        usados = set()
        for i, (x1,y1,r1) in enumerate (circulos):
            if i in usados:
                continue
            demasiado_cercano = False
            if 0 <= x1 < self.imagen.shape[1] and 0 <= y1 < self.imagen.shape[0]:
                intensidad1 = self.imagen[y1,x1] 
            else:
                intensidad1 = 0
            for j, (x2,y2,r2) in enumerate (circulos):
                if i != j and j not in usados:
                    if 0 <= x2 < self.imagen.shape[1] and 0 <= y2 < self.imagen.shape[0]:
                        intensidad2 = self.imagen[y2,x2]  
                    else:
                        intensidad2 = 0
                    distancia = np.sqrt ((x1-x2)** 2 + (y1-y2)**2)
                    #Condición para eliminar puntos cercanos entre si o cerca de puntos de mayor intensidad
                    if distancia < max(self.distancia_minima, r1+r2) or (distancia < 2 * r1 and intensidad2 > intensidad1):
                        demasiado_cercano = True
                        usados.add(j)
            if not demasiado_cercano and self.region_roi(x1,y1):
                filtrados.append ((x1,y1,r1))
        return np.array(filtrados)
    
    #Función para obtener la imagen procesada
    def obtener_imagen_procesada (self):
        return self.imagen_procesada
    
    #Función para saber si el punto (x,y) se encuentra dentro del ROI o no hay región ROI definida
    def region_roi(self,x,y):
        if self.roi is None:
            return True
        x_min, y_min, x_max, y_max = self.roi
        return x_min <= x <= x_max and y_min <= y <= y_max
    
    #Función que calcula en que bloque se encuentra un círculo
    def calcular_info_bloque(self, x, y ,r, intensidad):
        altura, ancho = self.imagen.shape
        bloque_altura = altura // self.num_filas
        bloque_anchura = ancho // self.num_columnas
        fila = y // bloque_altura + 1 #Calculo fila
        columna = x // bloque_anchura + 1 #Calculo columna
        bloque = (fila - 1) * self.num_columnas + columna #Calcular bloque
        diametro = 2 * r
        self.info_bloque.append({
                "x":x,
                "y":y,
                "r":r,
                "intensidad": intensidad,
                "fila":fila,
                "columna":columna,
                "bloque":bloque,
                "diametro": diametro,
            }) 
    #Función para mostrar por consola la información de cada punto
    def mostrar_bloque_info (self):
        #Ordenar por bloque primero y después por columna en orden ascendente
        self.info_bloque = sorted(self.info_bloque, key=lambda x: (x['bloque'], x['columna']))
        #Mostrar las coordenadas, fila, columna y bloque de cada punto
        for i, info in enumerate(self.info_bloque, start=1):
            print(f"Punto {i}: (x: {info['x']}, y: {info['y']}, Intensidad: {info['intensidad']}, Diámetro: {info['diametro']}) - Bloque: {info['bloque']} , Fila: {info['fila']}, Columna: {info['columna']}")
        print(f"Total de puntos encontrados {len(self.info_bloque)}")

#Coordinadas aproximadas del ROI
roi = (176, 255, 3027, 3047)

#Procesar las imágenes TIFF cargadas
imagenes = [
   #"LecheCompV1_005_A_220620_R70.tif",
   # "LecheCompV1_005_C_220620_G80.tif",
   # "LecheCompV1_005_C_220620_R70.tif",
   # "LecheCompV1_005_D_220620_G80.tif",
   # "LecheCompV1_005_D_220620_R70.tif",
   # "LecheCompV1_005_B_220620_R70.tif",
   # "LecheCompV1_001_C_220610_G70.tif",
   # "LecheCompV1_001_C_220610_R80.tif",
   # "LecheCompV1_001_D_220610_G80.tif",
   # "LecheCompV1_001_D_220610_R90.tif",
   # "LecheCompV1_002_A_220615_G70.tif",
   # "LecheCompV1_002_B_220615_G60.tif"
 ]

#Procesar todas las imagenes cargadas 
resultados = []
for ruta in imagenes:
    print(f"\nProcesando {ruta} ...")
    puntos = ObtenerPuntos(ruta, dimension_bloque=100, distancia_minima= 20, roi = roi)
    puntos.suavizar_y_quitar_ruido()
    puntos.procesar_imagen()
    puntos.mostrar_bloque_info()
    resultados.append(puntos.info_bloque)