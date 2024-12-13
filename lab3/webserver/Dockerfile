FROM python:3.11-slim

# Install ping utility
RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt wait-for-it.sh ./
RUN pip install --no-cache-dir -r requirements.txt && chmod +x wait-for-it.sh
COPY . .
EXPOSE 5000
CMD ["./wait-for-it.sh", "db:5432", "--", "python", "main.py"]
