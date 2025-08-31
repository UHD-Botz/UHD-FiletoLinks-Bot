FROM python:3.10-slim-buster
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -U pip && pip3 install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3","bot.py"]
