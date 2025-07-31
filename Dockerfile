# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies for building
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies (cache this layer)
COPY requirements.txt /app/
WORKDIR /app
RUN pip install --upgrade pip && pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG False

# Install runtime dependencies only
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r django && useradd -r -g django django

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy project (cache this layer separately)
COPY . /app/

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R django:django /app \
    && chmod -R 755 /app/staticfiles /app/media

# Remove existing staticfiles to ensure fresh collection during build
RUN rm -rf /app/staticfiles/*

# Switch to django user
USER django

# Create startup script with proper environment handling
RUN echo '#!/bin/bash\n\
# Run migrations\n\
python manage.py migrate --noinput\n\
\n\
# Debug static files configuration\n\
echo "Debugging static files configuration..."\n\
python manage.py debug_static\n\
\n\
# Always collect static files (this will upload to Cloudinary in production)\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput --clear --verbosity=2\n\
\n\
# Verify static files were collected\n\
echo "Static files collected:"\n\
ls -la /app/staticfiles/ || echo "No staticfiles directory"\n\
ls -la /app/staticfiles/admin/ || echo "No admin directory"\n\
\n\
# Start Gunicorn\n\
exec gunicorn eesa_backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port (will be overridden by Render)
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/admin/ || exit 1

# Start Gunicorn server
CMD ["/app/start.sh"] 