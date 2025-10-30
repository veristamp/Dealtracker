import uvicorn
import threading
import time
import webbrowser


def run_server():
    """Runs the FastAPI server in a separate thread."""
    uvicorn.run("client.api:app", host="0.0.0.0", port=8001, log_level="info")

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Server starting...")
    time.sleep(5) 
    
    url = "http://127.0.0.1:8001"
    print(f"Opening application in your browser at {url}")
    webbrowser.open(url)
    
    print("Server is running in the background. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server.")