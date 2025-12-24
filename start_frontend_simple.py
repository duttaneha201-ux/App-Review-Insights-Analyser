"""
Simple HTTP server to serve the standalone HTML frontend

Run this instead of Next.js if you have Node.js version issues.
"""

import http.server
import socketserver
import webbrowser
import os

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Get the frontend directory path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_dir = os.path.join(script_dir, 'frontend')
        super().__init__(*args, directory=frontend_dir, **kwargs)

def start_server():
    """Start a simple HTTP server to serve the frontend"""
    # Change to frontend directory so relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(script_dir, 'frontend')
    os.chdir(frontend_dir)
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("=" * 70)
        print("Frontend Server Started!")
        print("=" * 70)
        print(f"\nFrontend UI: http://localhost:{PORT}")
        print(f"Backend API: http://localhost:8000")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 70)
        
        # Open browser automatically
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")

if __name__ == "__main__":
    start_server()




