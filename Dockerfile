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
set -e\n\
echo "🔄 Setting up fresh database..."\n\
\n\
# Generate migrations for core apps first (those without dependencies)\n\
echo "📝 Creating migrations for accounts app..."\n\
python manage.py makemigrations accounts || echo "No changes detected for accounts"\n\
\n\
# Generate migrations for all apps\n\
echo "📝 Creating migrations for all apps..."\n\
python manage.py makemigrations || echo "No changes detected"\n\
\n\
# Run migrations\n\
echo "🗄️ Running migrations..."\n\
python manage.py migrate --noinput\n\
\n\
# Initialize cache system\n\
echo "🔄 Initializing cache..."\n\
python manage.py init_cache || echo "Cache initialization skipped"\n\
\n\
# Apply production indexes (after migrations complete)\n\
echo "📊 Applying production indexes..."\n\
python manage.py apply_production_indexes --force || echo "Academics indexes skipped or failed"\n\
python manage.py apply_accounts_indexes || echo "Accounts indexes skipped or failed"\n\
python manage.py apply_events_indexes || echo "Events indexes skipped or failed"\n\
python manage.py apply_projects_indexes || echo "Projects indexes skipped or failed"\n\
python manage.py apply_gallery_indexes || echo "Gallery indexes skipped or failed"\n\
python manage.py apply_placements_indexes || echo "Placements indexes skipped or failed"\n\
python manage.py apply_alumni_indexes || echo "Alumni indexes skipped or failed"\n\
python manage.py apply_careers_indexes || echo "Careers indexes skipped or failed"\n\
\n\
# Collect static files (Cloudinary handles them automatically)\n\
echo "📦 Collecting static files..."\n\
python manage.py collectstatic --noinput\n\
\n\
# Start Gunicorn\n\
echo "🚀 Starting server..."\n\
exec gunicorn eesa_backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port (will be overridden by Render)
EXPOSE 8000

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/admin/ || exit 1

# Start Gunicorn server
CMD ["/app/start.sh"] 