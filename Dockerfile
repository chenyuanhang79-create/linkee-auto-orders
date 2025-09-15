FROM python:3.11-slim
RUN apt-get update && apt-get install -y chromium chromium-driver && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server.py .
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PORT=8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "server:app"]
