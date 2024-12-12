import os
import time
import threading
import requests
import pika
from flask import Flask, request, jsonify
from ftplib import FTP
from threading import Lock

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
FTP_HOST = os.environ.get('FTP_HOST', 'ftp_server')
LEADER_UPDATE_PORT = int(os.environ.get('LEADER_UPDATE_PORT', 4000))

leader_host = None
leader_lock = Lock()

app = Flask(__name__)

@app.route('/update-leader', methods=['POST'])
def update_leader():
    global leader_host
    data = request.get_json()
    new_leader = data.get('leader_host')
    if not new_leader:
        return jsonify({"error": "No leader_host provided"}), 400
    with leader_lock:
        leader_host = new_leader
    return jsonify({"message": "Leader updated", "leader": leader_host}), 200

def consume_rabbitmq():
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='scraped_data')

    def callback(ch, method, properties, body):
        data_str = body.decode('utf-8')
        with leader_lock:
            if leader_host:
                try:
                    requests.post(f"{leader_host}/resource", json={"data": data_str})
                except Exception as e:
                    print("Error posting to leader:", e)

    channel.basic_consume(queue='scraped_data', on_message_callback=callback, auto_ack=True)
    print("Manager: Starting RabbitMQ consumer...")
    channel.start_consuming()

def ftp_fetch():
    while True:
        time.sleep(30)
        print("Manager: Fetching file from FTP...")
        try:
            ftp = FTP(FTP_HOST)
            ftp.login('user', 'pass')
            with open('fetched_file.json', 'wb') as f:
                ftp.retrbinary('RETR data.json', f.write)
            ftp.quit()

            with open('fetched_file.json', 'r') as f:
                file_data = f.read()

            with leader_lock:
                if leader_host:
                    try:
                        requests.post(f"{leader_host}/resource", json={"data": file_data})
                    except Exception as e:
                        print("Error posting FTP data to leader:", e)
        except Exception as e:
            print("Error fetching from FTP:", e)


if __name__ == "__main__":
    # Start rabbitmq consumer in a thread
    t_rabbit = threading.Thread(target=consume_rabbitmq, daemon=True)
    t_rabbit.start()

    # Start ftp fetcher in a thread
    t_ftp = threading.Thread(target=ftp_fetch, daemon=True)
    t_ftp.start()

    app.run(host='0.0.0.0', port=LEADER_UPDATE_PORT)
