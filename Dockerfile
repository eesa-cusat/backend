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
ENV DOCKER_BUILD 1

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
RUN rm -rf /app/staticfiles/* || true

# Switch to django user
USER django

# Note: Static files will be uploaded at runtime when environment variables are available

# Create startup script with proper environment handling
RUN echo '#!/bin/bash\n\
# Run migrations\n\
python manage.py migrate --noinput\n\
\n\
# Upload static files to Cloudinary if environment variables are available\n\
if [ -n "$CLOUDINARY_CLOUD_NAME" ] && [ -n "$CLOUDINARY_API_KEY" ] && [ -n "$CLOUDINARY_API_SECRET" ]; then\n\
    echo "Uploading static files to Cloudinary..."\n\
    python manage.py shell -c "from eesa_backend.management.commands.upload_static_to_cloudinary import Command; cmd = Command(); cmd.handle(clear=True)"\n\
else\n\
    echo "Cloudinary environment variables not available, skipping static file upload"\n\
fi\n\
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