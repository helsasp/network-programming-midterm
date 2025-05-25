import logging
import shlex
import json

from file_interface import FileInterface


class FileProtocol:
    def __init__(self):
        self.file_handler = FileInterface()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def string_execute(self, input_command=''):
        logging.info(f"Incoming command: {input_command[:100]}..." if len(input_command) > 100 else input_command)

        try:
            tokens = input_command.split(' ', 2)
            command_name = tokens[0].strip().lower()

            logging.info(f"Handling command: {command_name}")

            if command_name == "list":
                arguments = []
            elif command_name in ["get", "delete"]:
                arguments = [tokens[1]] if len(tokens) > 1 else []
            elif command_name == "add":
                if len(tokens) < 3:
                    return json.dumps(dict(status='FAILED', data='ADD command needs filename and file content'))

                file_name = tokens[1]
                file_data = tokens[2]
                arguments = [file_name, file_data]
            else:
                return json.dumps(dict(status='FAILED', data='Unrecognized command'))

            result_data = getattr(self.file_handler, command_name)(arguments)

            json_response = json.dumps(result_data)
            logging.info(f"Response size: {len(json_response)} bytes")

            return json_response

        except Exception as error:
            logging.error(f"Command processing failed: {str(error)}")
            return json.dumps(dict(status='FAILED', data=f'Exception: {str(error)}'))


if __name__ == '__main__':
    # usage example
    protocol = FileProtocol()
    print(protocol.string_execute("LIST"))
