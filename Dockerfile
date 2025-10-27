FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy only what is needed to install the package.
COPY pyproject.toml README.md requirements.txt ./
COPY progressista progressista

RUN pip install --no-cache-dir .

EXPOSE 8000

ENV PROGRESSISTA_HOST=0.0.0.0 \
    PROGRESSISTA_PORT=8000

CMD ["progressista", "serve", "--host", "0.0.0.0", "--port", "8000"]
