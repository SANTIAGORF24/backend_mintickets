# Usa una imagen base de Python
FROM python:3.9-slim

# Configura el directorio de trabajo
WORKDIR /app

# Copia los archivos necesarios
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

# Expone el puerto que la aplicación Flask usará
EXPOSE 5000

# Define el comando por defecto
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
