import os
import threading
from app import create_app, db
from raft.raft_node import RaftNode

app = create_app()

NODE_ID = int(os.environ["NODE_ID"])
PEER_IDS = os.environ.get("PEER_IDS", "")
MANAGER_URL = os.environ.get("MANAGER_URL", "http://manager:4000/update-leader")

# Parse peers: we have to form something like [("webserver2", 3002)] for node_id=1 and peer_id=2
peers = []
if PEER_IDS.strip():
    for pid_str in PEER_IDS.split(","):
        pid = int(pid_str.strip())
        peer_host = f"webserver{pid}"
        peer_port = 3000 + pid
        peers.append((peer_host, peer_port))

# Create DB schema only for one node to avoid conflicts
if NODE_ID == 1:
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print("Warning: Could not create tables (possibly already exist)", e)

print(f"Node_id:{NODE_ID}, peers:{peers}, manager_url:{MANAGER_URL}")
node = RaftNode(NODE_ID, peers, MANAGER_URL)
print("node_started")
node.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
