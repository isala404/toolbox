import socket
import threading

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

if __name__ == '__main__':
    tcp_server = threading.Thread(target=tcp_echo_server)
    udp_server = threading.Thread(target=udp_echo_server)

    tcp_server.start()
    udp_server.start()

    tcp_server.join()
    udp_server.join()
