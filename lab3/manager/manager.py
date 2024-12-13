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
    try:
        credentials = pika.PlainCredentials('user', 'pass')  # match docker-compose credentials
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue='scraped_data')
    except Exception as e:
        print(f"Error in consume_rabbitmq:{e}")

    def callback(ch, method, properties, body):
        print("Callback was called")
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
    print("FTP function started at least or what?")
    while True:
        print("Entering while loop...")
        time.sleep(10)
        print("Manager: Fetching file from FTP...")
        try:
            print(f"Connecting to FTP server {FTP_HOST}...")
            ftp = FTP(FTP_HOST)
            print("FTP object created. Attempting login...")
            ftp.login('user', 'pass')
            print("Login successful. Fetching file...")
            with open('fetched_file.json', 'wb') as f:
                ftp.retrbinary('RETR data.json', f.write)
            print("File retrieved. Closing connection...")
            ftp.quit()

            print("Reading the content of fetched_file")
            with open('fetched_file.json', 'r') as f:
                file_data = f.read()
            
            print(file_data)
            
            print("Read file. Checking for leader_host...")
            with leader_lock:
                print(f"Current leader host:{leader_host}")
                if leader_host:
                    print(f"Sending data to leader: {leader_host}")
                    try:
                        requests.post(f"{leader_host}/resource", json={"data": file_data})
                    except Exception as e:
                        print("Error posting FTP data to leader:", e)
        except Exception as e:
            print("Error fetching from FTP:", e)



if __name__ == "__main__":
    print("Manager: Waiting before starting threads...")
    time.sleep(25)
    print("Manager: Starting threads now.")
    print("Manager: Started consumer thread")
    t_rabbit = threading.Thread(target=consume_rabbitmq, daemon=True)
    t_rabbit.start()

    print("Manager: Starting ftp thread")
    t_ftp = threading.Thread(target=ftp_fetch, daemon=True)
    t_ftp.start()

    app.run(host='0.0.0.0', port=LEADER_UPDATE_PORT)
