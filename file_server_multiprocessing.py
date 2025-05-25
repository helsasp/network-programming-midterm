from socket import *
import socket
import threading
import logging
import time
import sys
import multiprocessing
from multiprocessing import Process, Queue, Pool
import io

from file_protocol import FileProtocol

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

protocol_handler = FileProtocol()

def handle_client_connection(client_pair):
    conn, client_addr = client_pair
    data_buffer = b''

    try:
        logging.info(f"Handling client at {client_addr}")
        while True:
            received_chunk = conn.recv(2**20)
            if not received_chunk:
                break

            data_buffer += received_chunk

            if b"\r\n\r\n" in data_buffer:
                request_text = data_buffer.decode()
                logging.info(f"Full request from {client_addr} received ({len(data_buffer)} bytes)")

                start = time.time()
                result = protocol_handler.string_execute(request_text.strip())
                end = time.time()

                logging.info(f"Processed in {end - start:.2f} seconds")

                final_response = result + "\r\n\r\n"
                response_bytes = final_response.encode()
                total_length = len(response_bytes)
                logging.info(f"Sending {total_length} bytes back")

                chunk_size = 2**16
                for i in range(0, total_length, chunk_size):
                    conn.sendall(response_bytes[i:i+chunk_size])

                logging.info(f"Response sent to {client_addr}")
                data_buffer = b''

    except Exception as ex:
        logging.error(f"Error with client {client_addr}: {ex}")
    finally:
        logging.info(f"Closing connection with {client_addr}")
        conn.close()

class ThreadedServer:
    def __init__(self, host='0.0.0.0', port=6666, workers=10):
        self.server_address = (host, port)
        self.worker_count = workers

    def dispatch_request(self, conn, client_addr):
        handle_client_connection((conn, client_addr))

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**20)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2**20)

        logging.warning(f"Server listening on {self.server_address}")
        server_socket.bind(self.server_address)
        server_socket.listen(10)

        pool = multiprocessing.Pool(processes=self.worker_count)

        try:
            while True:
                conn, client_addr = server_socket.accept()
                proc = Process(target=self.dispatch_request, args=(conn, client_addr))
                proc.daemon = True
                proc.start()
                conn.close()
        except KeyboardInterrupt:
            logging.warning("Server shutting down.")
        finally:
            pool.close()
            pool.join()
            server_socket.close()

def run_server():
    if len(sys.argv) > 1:
        try:
            workers = int(sys.argv[1])
            if workers <= 0:
                raise ValueError("Worker count must be positive.")
        except ValueError as ve:
            print(f"Invalid input: {ve}. Using default of 10.")
            workers = 10
    else:
        workers = 10

    app_server = ThreadedServer(host='0.0.0.0', port=13337, workers=workers)
    app_server.start()

if __name__ == "__main__":
    run_server()
