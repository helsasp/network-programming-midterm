from socket import create_connection
import json
import base64
import os
import time

server_address = ('127.0.0.1', 13337)

def send_command(command_str):
    try:
        with create_connection(server_address, timeout=300) as sock:
            sock.sendall(command_str.encode())

            data_received = b""
            end_marker = b"\r\n\r\n"

            while True:
                chunk = sock.recv(2**20)
                if not chunk:
                    break
                data_received += chunk
                if end_marker in data_received[-8:]:
                    break

            response_str = data_received.decode().strip()
            return json.loads(response_str)
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "ERROR", "data": str(e)}

def list_files():
    result = send_command("LIST\r\n\r\n")
    if result['status'] == 'OK':
        print("Daftar file:")
        for i, name in enumerate(result['data'], 1):
            print(f"{i}. {name}")
    else:
        print(f"Gagal: {result.get('data')}")

def download_file(filename):
    result = send_command(f"GET {filename}\r\n\r\n")
    if result['status'] == 'OK':
        content = base64.b64decode(result['data_file'])
        with open(result['data_namafile'], 'wb') as f:
            f.write(content)
        print(f"File {filename} berhasil didownload ({len(content)} bytes)")
    else:
        print(f"Gagal: {result.get('data')}")

def upload_file(filename):
    if not os.path.exists(filename):
        print(f"File {filename} tidak ditemukan!")
        return

    with open(filename, 'rb') as f:
        content = base64.b64encode(f.read()).decode()

    command = f"ADD {filename} {content}\r\n\r\n"
    result = send_command(command)
    if result['status'] == 'OK':
        print(f"File {filename} berhasil diupload")
    else:
        print(f"Gagal upload: {result.get('data')}")

def delete_file(filename):
    result = send_command(f"DELETE {filename}\r\n\r\n")
    if result['status'] == 'OK':
        print(f"File {filename} berhasil dihapus")
    else:
        print(f"Gagal: {result.get('data')}")

def interactive_download():
    result = send_command("LIST\r\n\r\n")
    if result['status'] == 'OK':
        files = result['data']
        if not files:
            print("Tidak ada file untuk didownload")
            return

        print("File tersedia:")
        for i, name in enumerate(files, 1):
            print(f"{i}. {name}")

        while True:
            choice = input("Pilih nomor file (atau 'q' untuk keluar): ").strip()
            if choice.lower() == 'q':
                break
            try:
                index = int(choice) - 1
                if 0 <= index < len(files):
                    download_file(files[index])
                    break
                else:
                    print("Nomor tidak valid")
            except ValueError:
                print("Masukkan angka yang valid")
    else:
        print(f"Gagal ambil daftar file: {result.get('data')}")

def main():
    print("=== File Client ===")
    while True:
        try:
            user_input = input("\nPerintah (list/get/upload/delete/download/quit): ").strip()
            if not user_input:
                continue

            parts = user_input.split(maxsplit=1)
            cmd = parts[0].upper()

            if cmd == "LIST":
                list_files()
            elif cmd == "GET":
                if len(parts) < 2:
                    print("Gunakan: GET <nama_file>")
                else:
                    download_file(parts[1])
            elif cmd == "UPLOAD":
                if len(parts) < 2:
                    print("Gunakan: UPLOAD <nama_file>")
                else:
                    upload_file(parts[1])
            elif cmd == "DELETE":
                if len(parts) < 2:
                    print("Gunakan: DELETE <nama_file>")
                else:
                    delete_file(parts[1])
            elif cmd == "DOWNLOAD":
                interactive_download()
            elif cmd == "QUIT":
                print("Keluar...")
                break
            else:
                print("Perintah tidak dikenal.")
        except KeyboardInterrupt:
            print("\nKeluar...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
