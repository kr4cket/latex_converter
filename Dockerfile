FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
	apt-get install -y \
	libgl1 \
	libglib2.0-0 \
	libsm6 \
	libxrender1 \
	libxext6 \
	build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libxrender-dev \
    libgl1-mesa-dev \
	&& apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir -r requirements.txt

COPY definitions.py .
COPY config/ config
COPY app/ app
COPY ui/ ui
COPY alembic.ini .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--timeout-keep-alive", "60"]
