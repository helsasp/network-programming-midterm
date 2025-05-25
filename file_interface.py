import os
import json
import base64
from glob import glob
import logging


class FileInterface:

    def __init__(self):
        # Create directory if missing and change working directory
        if not os.path.isdir('files'):
            os.mkdir('files')
        os.chdir('files')
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def list(self, params=None):
        if params is None:
            params = []
        try:
            matched_files = glob('*.*')
            return {'status': 'OK', 'data': matched_files}
        except Exception as exc:
            logging.error(f"Failed to list files: {exc}")
            return {'status': 'ERROR', 'data': str(exc)}

    def get(self, params=None):
        if params is None:
            params = []
        try:
            if not params:
                logging.error("GET operation missing filename parameter")
                return {'status': 'ERROR', 'data': 'No filename provided'}

            file_name = params[0]
            logging.info(f"GET request received for file: {file_name}")

            if not os.path.isfile(file_name):
                logging.error(f"File '{file_name}' does not exist")
                return {'status': 'ERROR', 'data': f"File {file_name} not found"}

            file_size = os.path.getsize(file_name)
            logging.info(f"File size: {file_size} bytes")

            with open(file_name, 'rb') as file_handle:
                raw_content = file_handle.read()

            encoded_content = base64.b64encode(raw_content).decode()
            logging.info(f"Encoded content length: {len(encoded_content)} characters")

            return {'status': 'OK', 'data_namafile': file_name, 'data_file': encoded_content}

        except Exception as err:
            logging.error(f"Unexpected error during GET: {err}")
            return {'status': 'ERROR', 'data': str(err)}

    def add(self, params=None):
        if params is None:
            params = []
        if len(params) < 2:
            return {'status': 'ERROR', 'data': 'Parameter tidak lengkap'}

        try:
            new_file_name = params[0]
            b64_content = params[1]

            logging.info(f"Uploading file: {new_file_name}")
            logging.info(f"Encoded data size: {len(b64_content)}")

            try:
                decoded_bytes = base64.b64decode(b64_content)
            except Exception as decode_err:
                logging.error(f"Failed to decode base64: {decode_err}")
                return {'status': 'ERROR', 'data': f"Base64 decoding error: {decode_err}"}

            with open(new_file_name, 'wb') as out_file:
                out_file.write(decoded_bytes)

            if os.path.isfile(new_file_name):
                size_written = os.path.getsize(new_file_name)
                logging.info(f"File saved successfully, size: {size_written} bytes")
                return {'status': 'OK', 'data': f"File {new_file_name} berhasil diupload ({size_written} bytes)"}
            else:
                logging.error(f"Failed to write file {new_file_name}")
                return {'status': 'ERROR', 'data': f"File {new_file_name} gagal diupload"}

        except Exception as exc:
            logging.error(f"Error during ADD operation: {exc}")
            return {'status': 'ERROR', 'data': str(exc)}

    def delete(self, params=None):
        if params is None:
            params = []
        try:
            if not params:
                return {'status': 'ERROR', 'data': 'No filename provided'}

            target_file = params[0]

            if not os.path.isfile(target_file):
                return {'status': 'ERROR', 'data': f"File {target_file} not found"}

            os.remove(target_file)
            logging.info(f"Deleted file: {target_file}")

            if os.path.exists(target_file):
                logging.error(f"Could not delete file: {target_file}")
                return {'status': 'ERROR', 'data': f"File {target_file} gagal dihapus"}

            return {'status': 'OK', 'data': f"File {target_file} berhasil dihapus"}

        except Exception as exc:
            logging.error(f"Error during DELETE operation: {exc}")
            return {'status': 'ERROR', 'data': str(exc)}


if __name__ == '__main__':
    interface = FileInterface()
    print(interface.list())
