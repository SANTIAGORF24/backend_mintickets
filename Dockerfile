# Usa una imagen base de Python
FROM python:3.11-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de requisitos a la imagen
COPY requirements.txt ./

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido de tu aplicación al contenedor
COPY . .

# Expone el puerto en el que la aplicación correrá
EXPOSE 5000

# Define la variable de entorno para Flask
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Comando para ejecutar la aplicación
CMD ["flask", "run", "--host=0.0.0.0"]
