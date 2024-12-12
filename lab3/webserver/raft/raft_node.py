import socket
import threading
import time
import json
import requests
import random

class RaftNode:
    def __init__(self, node_id, peers, manager_update_url):
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
        threading.Thread(target=self.listen, daemon=True).start()
        threading.Thread(target=self.run_election_timer, daemon=True).start()

    def run_election_timer(self):
        while self.running:
            timeout = random.uniform(5.0, 10.0)
            start_time = time.time()
            while time.time() - start_time < timeout and not self.heartbeat_received:
                time.sleep(0.1)
            if not self.heartbeat_received:
                self.start_election()
            self.heartbeat_received = False

    def start_election(self):
        with self.lock:
            self.state = "Candidate"
            self.current_term += 1
            self.voted_for = self.node_id
            self.votes = 1
        request_vote_msg = {"type":"RequestVote","term":self.current_term,"candidate_id":self.node_id}
        self.broadcast(request_vote_msg)
        # wait for votes
        time.sleep(3)
        with self.lock:
            if self.votes > (len(self.peers)+1)//2 and self.state == "Candidate":
                self.become_leader()

    def become_leader(self):
        with self.lock:
            self.state = "Leader"
        print(f"Node {self.node_id} became leader")
        # Notify manager
        # Let's assume webserver runs on port 5000: host can be "http://webserverX:5000"
        leader_host = f"http://webserver{self.node_id}:5000"
        try:
            requests.post(self.manager_update_url, json={"leader_host": leader_host})
        except Exception as e:
            print("Error notifying manager of leadership:", e)
        threading.Thread(target=self.send_heartbeats, daemon=True).start()

    def send_heartbeats(self):
        while self.state == "Leader" and self.running:
            heartbeat_msg = {"type":"AppendEntries","term":self.current_term,"leader_id":self.node_id}
            self.broadcast(heartbeat_msg)
            time.sleep(2)

    def broadcast(self, message):
        data = json.dumps(message).encode('utf-8')
        for p in self.peers:
            self.server_socket.sendto(data, p)

    def listen(self):
        while self.running:
            data, addr = self.server_socket.recvfrom(1024)
            msg = json.loads(data.decode('utf-8'))
            msg_type = msg.get('type')
            if msg_type == "AppendEntries":
                self.handle_append_entries(msg)
            elif msg_type == "RequestVote":
                self.handle_request_vote(msg)
            elif msg_type == "RequestVoteResponse":
                self.handle_request_vote_response(msg)

    def handle_append_entries(self, msg):
        with self.lock:
            if msg['term'] >= self.current_term:
                self.current_term = msg['term']
                self.state = "Follower"
                self.voted_for = None
            self.heartbeat_received = True

    def handle_request_vote(self, msg):
        with self.lock:
            if msg['term'] > self.current_term:
                self.current_term = msg['term']
                self.voted_for = None
                self.state = "Follower"
            vote_granted = False
            if (self.voted_for is None or self.voted_for == msg['candidate_id']) and msg['term'] >= self.current_term:
                self.voted_for = msg['candidate_id']
                vote_granted = True
            response = {"type":"RequestVoteResponse","term":self.current_term,"vote_granted":vote_granted,"candidate_id":msg['candidate_id']}
            self.server_socket.sendto(json.dumps(response).encode('utf-8'), (self.get_peer_addr(msg['candidate_id'])))

    def handle_request_vote_response(self, msg):
        if self.state == "Candidate" and msg.get('vote_granted'):
            with self.lock:
                self.votes += 1

    def get_peer_addr(self, peer_id):
        for p in self.peers:
            # p is (host, port)
            # We know peers by their node_id indirectly. If you name them by index:
            # If node_id=2, then host might be webserver2 at port 3002
            # Let's guess from node_id:
            if p[1] == 3000+peer_id:
                return p
        return None
