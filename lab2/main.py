import threading
from app import create_app, db
import asyncio
import websockets
from app.routes.chat import websocket_handler

my_app = create_app()

# Run HTTP server
def run_http_server():
    with my_app.app_context():
        db.create_all()
    my_app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

# Run WebSocket server
async def run_websocket_server():
    print("Starting WebSocket server on ws://localhost:5001")
    async with websockets.serve(websocket_handler, "0.0.0.0", 5001):
        print("WebSocket server is running...")
        await asyncio.Future()  # Run forever


# Run both servers in separate threads
if __name__ == "__main__":
    # Thread for HTTP server
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()

    # Run WebSocket server on the main thread's event loop
    asyncio.run(run_websocket_server())
