## 💡 Autor y créditos

Desarrollado por Tatiana Mirela Cernea como parte del **Trabajo de Fin de Grado** en Ingeniería de Computadores.  
Agradecimientos al IRYCIS por el suministro de imágenes reales de microarrays.


# 🧪 ImagiQuantix

**ImagiQuantix** es una herramienta interactiva desarrollada en Python para la **detección, análisis y cuantificación automática de puntos de hibridación** en imágenes de microarrays, comúnmente utilizadas en el análisis de la expresión de anticuerpos IgE e IgG4 en entornos biomédicos.

---

## 🧠 Descripción del proyecto

Este software permite cargar imágenes en formato `.TIFF`, aplicar un conjunto de filtros y operaciones morfológicas, detectar puntos circulares mediante la transformada de Hough, y visualizar los resultados de forma interactiva en una interfaz gráfica intuitiva. Los usuarios pueden ajustar dinámicamente el umbral de sensibilidad, exportar coordenadas y obtener gráficas del rendimiento de detección.

---

## 📷 Características principales

- Carga y visualización de imágenes `.tif`
- Procesamiento de imagen con:
  - Filtro bilateral
  - Operaciones morfológicas (apertura y cierre)
  - Desenfoque Gaussiano
- Detección de círculos con `cv2.HoughCircles` (`cv2.HOUGH_GRADIENT_ALT`)
- Interfaz gráfica con `Tkinter`:
  - Visualización en tiempo real
  - Ajuste de umbral con `slider`
  - Exportación de coordenadas a `.txt`
  - Gráfica de evolución (umbral vs. puntos detectados)


