from socket import *
import socket
import threading
import logging
import time
import sys
from concurrent.futures import ThreadPoolExecutor
import io

from file_protocol import FileProtocol

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
file_proto = FileProtocol()


def client_process(sock_conn, client_addr):
    data_buffer = b''
    try:
        logging.info(f"Client {client_addr} connected and ready to process.")
        while True:
            packet = sock_conn.recv(2**20)
            if not packet:
                break

            data_buffer += packet

            if b"\r\n\r\n" in data_buffer:
                client_request = data_buffer.decode()
                logging.info(f"Received complete data from {client_addr} (size: {len(data_buffer)} bytes)")

                exec_start = time.time()
                result = file_proto.string_execute(client_request.strip())
                exec_end = time.time()

                logging.info(f"Execution time: {exec_end - exec_start:.2f} seconds")
                response_msg = result + "\r\n\r\n"

                byte_response = response_msg.encode()
                total_size = len(byte_response)

                logging.info(f"Sending back {total_size} bytes to {client_addr}")
                chunk_limit = 2**20
                for i in range(0, total_size, chunk_limit):
                    sock_conn.sendall(byte_response[i:i+chunk_limit])

                logging.info(f"All data sent successfully to {client_addr}")
                data_buffer = b''

    except Exception as err:
        logging.error(f"An error occurred while handling {client_addr}: {err}")
    finally:
        logging.info(f"Connection with {client_addr} is now closed.")
        sock_conn.close()


class Server:
    def __init__(self, ipaddress='0.0.0.0', port=13337, max_workers=10):
        self.addr_info = (ipaddress, port)
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**20)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2**20)
        self.worker_count = max_workers

    def run(self):
        logging.warning(f"Server is active on {self.addr_info}")
        self.listener.bind(self.addr_info)
        self.listener.listen(10)
        with ThreadPoolExecutor(max_workers=self.worker_count) as pool:
            try:
                while True:
                    conn_obj, addr_obj = self.listener.accept()
                    logging.warning(f"New client connection from {addr_obj}")
                    conn_obj.settimeout(300)
                    pool.submit(client_process, conn_obj, addr_obj)
            except KeyboardInterrupt:
                logging.warning("Terminating server... KeyboardInterrupt detected.")
            finally:
                self.listener.close()


def main():
    if len(sys.argv) > 1:
        try:
            num_workers = int(sys.argv[1])
            if num_workers <= 0:
                raise ValueError("Worker count must be greater than zero.")
        except ValueError as err_msg:
            print(f"Invalid input: {err_msg}. Defaulting to 10 workers.")
            num_workers = 10
    else:
        num_workers = 10

    service = Server(ipaddress='0.0.0.0', port=13337, max_workers=num_workers)
    service.run()


if __name__ == "__main__":
    main()
