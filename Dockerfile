FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional: build tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	&& rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Collect static at build time (optional; also done on start)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Run migrations on start, then launch the provided command (default gunicorn)
# Use the conventional "--" arg so that $@ correctly receives CMD/compose command args.
ENTRYPOINT ["/bin/sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput || true && exec \"$@\"", "--"]
CMD ["gunicorn", "earlypass.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
