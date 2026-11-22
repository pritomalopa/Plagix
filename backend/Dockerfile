FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies using precompiled binary wheels including python-multipart
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy psycopg[binary] alembic pydantic pydantic-settings python-dotenv redis celery passlib python-jose[cryptography] bcrypt email-validator pypdf python-docx python-multipart pytest pytest-asyncio httpx

# Copy application code
COPY . .

# Create non-root user and set permissions
RUN useradd -m -u 1000 plagix && chown -R plagix:plagix /app
USER plagix

# Expose port
EXPOSE 8000

# Health check using python
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"

# Run application with restricted reload directory
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "app"]
