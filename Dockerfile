# Dockerfile
FROM python:3.11-slim

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y libpq-dev gcc --no-install-recommends

# Arbeitsverzeichnis im Container
WORKDIR /app

# Requirements installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektdateien reinkopieren
COPY . .

# Port freigeben
EXPOSE 8000

# Startbefehl
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
