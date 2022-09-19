#  coding: utf-8 
import socketserver
import os
import datetime

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


class MyWebServer(socketserver.BaseRequestHandler):

    HTTP_ver = ""
    
    def handle(self):
        self.data = self.request.recv(1024).decode("utf-8").strip()
        request_dic, headers_dic = self.parse_request(self.data)
        print ("\nGot a request of: %s\n" % self.data)
        # self.request.sendall(bytearray("OK",'utf-8'))

        self.parse_path(request_dic)

        if not self.is_valid_method(request_dic["method"]):
            print('YEPPERS')
            self.res_405()
        elif not self.is_valid_path(request_dic["path"]):
            self.res_404()
        else:
            self.res_200(request_dic["content_type"])

    def parse_request(self, data):
        request_dic = {}
        headers_dic = {}
        lines = data.splitlines()
        # get our request method, path, and HTTP version
        request_dic["method"], request_dic["path"], self.HTTP_ver = str(lines[0]).split(' ')
        request_dic['content_type'] = ''

        # get our headers
        for line in lines[1:]:
            header, val = line.split(': ')
            headers_dic[header] = val

        return request_dic, headers_dic

    def parse_path(self, request_dic: dict):
        # determine content type to respond back with
        valid_content_types = {
            "css": "text/css",
            "html": "text/html"
        }

        split_path = request_dic["path"].split('/')

        if len(split_path[-1]) > 0:                                  # not just a delimeter
            end_file = split_path[-1].split('.')                     # get just the name of the file
            if len(end_file) == 2:                                   # is a file, with some file type e.g. something.css
                print(end_file)
                file_type = end_file[1]
                request_dic["content_type"] = valid_content_types[file_type]
            elif len(end_file) == 1:                                 # is not a file, directory is missing a slash at the end
                request_dic["path"] = request_dic["path"] + '/' + 'index.html'
                request_dic["content_type"] = valid_content_types["html"]
            else:
                request_dic["content_type"] = valid_content_types[file_type]


    def http_res_msg(self, status_code, headers, body=''):
        status_codes = {
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            405: "Method Not Allowed"
        }
        res_msg = []    

        # Status Code & Msg
        status_msg = f"{self.HTTP_ver} {status_code} {status_codes[status_code]}"
        res_msg.append(status_msg)

        res_msg.extend(headers)

        return '\r\n'.join(res_msg) + body

    def is_valid_path(self, path: str):
        if path[0] != '/':
            return False
        abs_root = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'www')          # get the absolute root directory of our www folder
        abs_path = f"{abs_root}/{path[1:]}"

        print(f"the path is {abs_path}")
        # check is file
        return os.path.isdir(abs_path) or os.path.isfile(abs_path)
        
    def is_valid_method(self, method: str):
        valid_methods = [
            'GET'
        ]
        return method in valid_methods

    def res_200(self, type):
        res_headers = []

        res_headers.append(f'Date: {self.get_current_date_time()}')
        if len(type) > 0:
            res_headers.append(f'Content-Type: {type}')
        res_headers.append(f'Connection: close')
        res_msg = self.http_res_msg(200, res_headers)
        
        self.request.sendall(bytearray(res_msg,'utf-8'))

    def res_404(self):
        res_headers = []
        res_msg = self.http_res_msg(404, res_headers)
        print(res_msg)
        self.request.sendall(bytearray(res_msg,'utf-8'))

    def res_405(self):
        res_headers = []
        res_msg = self.http_res_msg(405, res_headers)
        print(res_msg)
        self.request.sendall(bytearray(res_msg,'utf-8'))

    def get_current_date_time(self):
        return datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %Z")



if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
