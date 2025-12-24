FROM python:3.11-slim

# Optimisations Python pour Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Sécurité : Création d'un utilisateur non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Installation des dépendances (Layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Attribution des droits à l'utilisateur non-root
RUN chown -R appuser:appuser /app

# Passage à l'utilisateur sécurisé
USER appuser

EXPOSE 8000

# Healthcheck natif
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; response = urllib.request.urlopen('http://localhost:8000/health'); exit(0) if response.getcode() == 200 else exit(1)"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
