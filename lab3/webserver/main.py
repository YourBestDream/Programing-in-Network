import threading
import os
from app import create_app, db
from raft.raft_node import RaftNode

app = create_app()

def run_http_server():
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    node_id = int(os.getenv("NODE_ID", "1"))
    peer_ids_str = os.getenv("PEER_IDS", "")
    peer_ids = [int(x) for x in peer_ids_str.split(",") if x.strip()]

    # Peers are webserverX on UDP port 3000+X
    peers = []
    for pid in peer_ids:
        peers.append((f"webserver{pid}", 3000+pid))

    manager_url = os.getenv("MANAGER_URL", "http://manager:4000/update-leader")

    raft_node = RaftNode(node_id=node_id, peers=peers, manager_update_url=manager_url)
    raft_node.start()

    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()
    http_thread.join()
