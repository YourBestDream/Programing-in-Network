FROM python:3.11.6-slim

WORKDIR /app

COPY requirements.txt wait-for-it.sh ./


RUN pip install --no-cache-dir -r requirements.txt && \
    chmod +x wait-for-it.sh

COPY . .

EXPOSE 5000
CMD ["./wait-for-it.sh", "db:5432", "--", "flask", "run", "--host=0.0.0.0"]
