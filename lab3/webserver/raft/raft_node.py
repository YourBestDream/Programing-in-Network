import socket
import threading
import time
import json
import requests
import random

class RaftNode:
    def __init__(self, node_id, peers, manager_update_url):
        print(f"Initializing node {node_id}")
        self.node_id = node_id
        self.peers = peers  # list of (host, port)
        self.manager_update_url = manager_update_url
        self.current_term = 0
        self.voted_for = None
        self.state = "Follower"
        self.lock = threading.Lock()
        self.heartbeat_received = False
        self.running = True
        self.host = "0.0.0.0"
        self.port = 3000 + self.node_id
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))
        self.votes = 0

    def start(self):
        print(f"Node {self.node_id}: Starting node.")
        threading.Thread(target=self.listen, daemon=True).start()
        print(f"Node {self.node_id}: Started listening.")
        # Add a small random delay so both nodes don't start elections at the same time
        time.sleep(random.uniform(0.5, 1.5))
        threading.Thread(target=self.run_election_timer, daemon=True).start()
        print(f"Node {self.node_id}: Election timer started.")

    def run_election_timer(self):
        while self.running:
            timeout = random.uniform(1.5, 3.0)  # random election timeout
            print(f"Node {self.node_id}: Waiting for heartbeat or leader for {timeout:.2f} seconds. State={self.state}, Term={self.current_term}")
            start_time = time.time()
            self.heartbeat_received = False

            while time.time() - start_time < timeout and not self.heartbeat_received and self.state != "Leader":
                time.sleep(0.1)

            print(f"Node {self.node_id}: Timer expired or heartbeat/leader detected. heartbeat_received={self.heartbeat_received}, state={self.state}")
            # If no heartbeat and not leader, start election
            if not self.heartbeat_received and self.state != "Leader":
                print(f"Node {self.node_id}: No heartbeat received. Starting election.")
                self.start_election()

    def start_election(self):
        with self.lock:
            self.state = "Candidate"
            self.current_term += 1
            self.voted_for = self.node_id
            self.votes = 1

        request_vote_msg = {
            "type": "RequestVote",
            "term": self.current_term,
            "candidate_id": self.node_id
        }
        self.broadcast(request_vote_msg)
        print(f"Node {self.node_id}: Broadcasted RequestVote message. Current term: {self.current_term}")

    def become_leader(self):
        with self.lock:
            self.state = "Leader"
        print(f"Node {self.node_id} became leader in term {self.current_term}.")
        leader_host = f"http://webserver{self.node_id}:5000"
        try:
            r = requests.post(self.manager_update_url, json={"leader_host": leader_host}, timeout=2)
            print(f"Node {self.node_id}: Notified manager of leadership. Response: {r.status_code}")
        except Exception as e:
            print(f"Node {self.node_id}: Error notifying manager of leadership: {e}")

        # Send an immediate heartbeat before starting the periodic heartbeats
        self.send_heartbeat_once()
        threading.Thread(target=self.send_heartbeats, daemon=True).start()

    def send_heartbeats(self):
        while self.running and self.state == "Leader":
            time.sleep(1)
            self.send_heartbeat_once()

    def send_heartbeat_once(self):
        print(f"Node {self.node_id}: Sending heartbeats (term={self.current_term}).")
        heartbeat_msg = {
            "type": "AppendEntries",
            "term": self.current_term,
            "leader_id": self.node_id
        }
        self.broadcast(heartbeat_msg)

    def broadcast(self, message):
        data = json.dumps(message).encode('utf-8')
        for p in self.peers:
            print(f"Node {self.node_id}: Sending message to {p} -> {message}")
            self.server_socket.sendto(data, p)

    def listen(self):
        while self.running:
            data, addr = self.server_socket.recvfrom(1024)
            msg = json.loads(data.decode('utf-8'))
            print(f"Node {self.node_id}: Received message {msg} from {addr}. State={self.state}, Term={self.current_term}")
            msg_type = msg.get('type')
            if msg_type == "AppendEntries":
                self.handle_append_entries(msg)
            elif msg_type == "RequestVote":
                self.handle_request_vote(msg)
            elif msg_type == "RequestVoteResponse":
                self.handle_request_vote_response(msg)

    def handle_append_entries(self, msg):
        with self.lock:
            print(f"Node {self.node_id}: Handling AppendEntries. Incoming term={msg['term']}, current_term={self.current_term}")
            if msg['term'] > self.current_term:
                self.current_term = msg['term']
                self.voted_for = None
                self.state = "Follower"
            # Received a valid heartbeat
            if msg['term'] >= self.current_term:
                self.heartbeat_received = True
                if self.state != "Follower":
                    self.state = "Follower"

    def handle_request_vote(self, msg):
        with self.lock:
            print(f"Node {self.node_id}: Handling RequestVote. MsgTerm={msg['term']}, currentTerm={self.current_term}, voted_for={self.voted_for}")
            if msg['term'] > self.current_term:
                # Step down for higher term
                self.current_term = msg['term']
                self.voted_for = None
                self.state = "Follower"

            vote_granted = False
            if msg['term'] == self.current_term and (self.voted_for is None or self.voted_for == msg['candidate_id']):
                self.voted_for = msg['candidate_id']
                vote_granted = True

            response = {
                "type": "RequestVoteResponse",
                "term": self.current_term,
                "vote_granted": vote_granted,
                "candidate_id": msg['candidate_id']
            }
            candidate_addr = self.get_peer_addr(msg['candidate_id'])

            # **Important**: If we grant a vote, reset our election timer by simulating a heartbeat.
            if vote_granted:
                self.heartbeat_received = True

            if candidate_addr:
                print(f"Node {self.node_id}: Sending RequestVoteResponse {response} to {candidate_addr}.")
                self.server_socket.sendto(json.dumps(response).encode('utf-8'), candidate_addr)
            else:
                print(f"Node {self.node_id}: Could not find candidate_addr for {msg['candidate_id']}")

    def handle_request_vote_response(self, msg):
        with self.lock:
            print(f"Node {self.node_id}: Handling RequestVoteResponse. term={msg.get('term')}, currentTerm={self.current_term}, vote_granted={msg.get('vote_granted')}")
            if self.state == "Candidate" and msg.get('vote_granted') and msg.get('term') == self.current_term:
                self.votes += 1
                print(f"Node {self.node_id}: Vote granted. Total votes: {self.votes}.")
                needed_votes = (len(self.peers) + 1) // 2 + 1
                if self.votes >= needed_votes and self.state == "Candidate":
                    self.become_leader()

    def get_peer_addr(self, peer_id):
        for p in self.peers:
            if p[1] == 3000 + peer_id:
                return p
        return None
