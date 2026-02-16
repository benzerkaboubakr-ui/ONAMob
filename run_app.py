import os
import sys
import threading
import webbrowser
import time
from app import app, db

def open_browser():
    time.sleep(2)  # Wait for server to start
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Ensure database is created
    with app.app_context():
        db.create_all()
    
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Flask
    app.run(port=5000)
