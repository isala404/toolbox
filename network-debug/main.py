import socket
import threading
import struct
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# TCP Echo Server
def tcp_echo_server(host='0.0.0.0', port=5600):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(5)
    print(f'TCP Echo Server listening on {host}:{port}')

    while True:
        conn, addr = sock.accept()
        print(f'TCP connection from {addr}')
        data = conn.recv(1024)
        if not data:
            break
        print(f'Received data: {data.decode()}')
        conn.sendall(data)  # Echo the received data back
    conn.close()

# UDP Echo Server
def udp_echo_server(host='0.0.0.0', port=5700):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f'UDP Echo Server listening on {host}:{port}')

    while True:
        data, addr = sock.recvfrom(1024)
        print(f'Received data from {addr}: {data.decode()}')
        sock.sendto(data, addr)  # Echo the received data back

# HTTP Server with Reset Endpoint
class ResetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/reset'):
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            do_param = query_params.get('do', ['false'])[0].lower()
            
            if do_param == 'true':
                # Send RST packet
                self.send_reset()
            else:
                # Return 200 OK
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")

    def send_reset(self):
        # Get the client socket
        client_socket = self.request

        # Enable SO_LINGER with a timeout of 0 to send RST
        l_onoff = 1
        l_linger = 0
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 
                                 struct.pack('ii', l_onoff, l_linger))
        
        # Close the socket to trigger the RST
        client_socket.close()

def http_server(host='0.0.0.0', port=5800):
    server_address = (host, port)
    httpd = HTTPServer(server_address, ResetHandler)
    print(f'HTTP Server with Reset endpoint listening on {host}:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    tcp_server = threading.Thread(target=tcp_echo_server)
    udp_server = threading.Thread(target=udp_echo_server)
    reset_server = threading.Thread(target=http_server)

    tcp_server.start()
    udp_server.start()
    reset_server.start()

    tcp_server.join()
    udp_server.join()
    reset_server.join()
