import http.server
import socketserver

PORT = 8080

class AdminServer(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/admin/users':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'User management page')
        elif self.path == '/admin/devices':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Device management page')
        elif self.path == '/admin/settings':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'System settings page')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Page not found')

with socketserver.TCPServer(("", PORT), AdminServer) as httpd:
    print("Admin server started on port", PORT)
    httpd.serve_forever()