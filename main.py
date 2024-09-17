from http.server import BaseHTTPRequestHandler, HTTPServer
import json
# from werkzeug.serving import run_simple
from pymongo import MongoClient
from bson import json_util, objectid

from datetime import datetime
from categories import Categories
from routes_file import route_function
import logging


# def log_function(data,path):
#     logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     logger = logging.getLogger(__name__)
#     handler = logging.FileHandler(f"/logs/{path}-{datetime.now()}.log")
#     handler.setLevel(logging.DEBUG)
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    MAX_REQUEST_SIZE = 4 * 1024 * 1024

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def _set_response(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow requests from any origin
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Origin, Content-Type, Accept')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_response()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = b''
        while content_length > 0:
            chunk_size = min(content_length, 4096)
            chunk = self.rfile.read(chunk_size)
            post_data += chunk
            content_length -= len(chunk)
            # print('chunked')
        post_data = post_data.decode('utf-8')
        if self.path == '/cmsPurchaseOrderSaveQATest' or self.path == '/CmsPurchaseOrderGateEntryCreate':
            print(post_data)
        post_data = json.loads(post_data)
        response_data = route_function(post_data, self.path)
        self._set_response()
        self.wfile.write(json.dumps(response_data).encode())


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()       