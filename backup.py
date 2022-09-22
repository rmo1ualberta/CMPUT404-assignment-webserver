#  coding: utf-8 
import socketserver
import os
import datetime
import mimetypes

# Copyright 2022 Abram Hindle, Eddie Antonio Santos, Raymond Mo
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
# some of the code is Copyright © 2001-2022 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


class MyWebServer(socketserver.BaseRequestHandler):

    HTTP_ver = "HTTP/1.1"
    request_dic = {}
    headers_dic = {}
    
    def handle(self):
        self.data = self.request.recv(1024).decode("utf-8").strip()
        self.parse_request(self.data)
        print ("\nGot a request of: %s\n" % self.data)

        # check the request and response accordingly
        res_msg = ''
        if not self.is_valid_method(self.request_dic["method"]):
            res_msg = self.res_405()
        elif self.is_valid_path() and not self.is_valid_file() and not self.is_path_correct():
            res_msg = self.res_301()
        elif not (self.is_valid_path() or self.is_valid_file()):
            res_msg = self.res_404()
        else:
            res_msg = self.res_200()
        
        self.request.sendall(bytearray(res_msg,'utf-8'))

    def parse_request(self, data):
        """ Parses the given request line by getting the method, path, and the HTTP version.
            Adds that parsed data into two dictionaries, one for the request, and one for
            the requested headers.
        Args:
            data (_type_): The request data received by our server
        """
        lines = data.splitlines()
        # get our request method, path, and HTTP version
        self.request_dic["method"], self.request_dic["path"], self.HTTP_ver = str(lines[0]).split(' ')
        self.request_dic['content_type'] = ''

    def get_mime_type(self, path: str):
        """ Given a path to a file, returns the content-type needed for the HTTP response.

        Args:
            path (str): The string path to the file we want to get the mimetype from.

        Returns:
            The mime type, as a string.
        """
        file = path.split('/')[-1]
        mimetype = mimetypes.guess_type(file)
        return mimetype[0]

    def build_res_msg(self, status_code, headers, body=''):
        """Builds the HTTP response message to be send back to the user agent.

        Args:
            status_code (int): The status code
            headers (list): A list containing the headers to be sent back
            body (str, optional): String containing the entity body. Defaults to ''.

        Returns:
            A string of the fully built response message
        """
        status_codes = {
            200: "OK",
            301: "Moved Permanently",
            404: "Not Found",
            405: "Method Not Allowed"
        }
        res_msg = []    

        # Status Code & Msg
        status_msg = f"{self.HTTP_ver} {status_code} {status_codes[status_code]}"
        res_msg.append(status_msg)
        res_msg.extend(headers)
        res_msg.append("\r\n")

        return '\r\n'.join(res_msg) + body

    def is_valid_path(self):
        """Checks if the given path is an existing directory in www

        Returns:
            True if path exists
        """
        # normalize path to prevent attacks
        
        abs_norm_path = f'{os.path.abspath("www")}/{os.path.normpath(self.request_dic["path"])}'
        return os.path.isdir(abs_norm_path)
    
    def is_valid_file(self):
        """Checks if the given path to a file is an existing file in www or its subdirectories

        Returns:
            True if file exists
        """
        return os.path.isfile(self.get_abs_norm_path())

    def is_path_correct(self):
        """Checks if the path is correct; in that it has an ending slash

        Returns:
            True if correct
        """
        return self.request_dic["path"][-1] == '/'         
        
    def is_valid_method(self, method: str):
        """Checks if the given method is valid

        Args:
            method (str): The method given in the request

        Returns:
            True if the method given is correct
        """
        valid_methods = [
            'GET'
        ]
        # print(f"The method is {method} and valid = {method in valid_methods}")
        return method in valid_methods

    def res_200(self):
        """ Builds a 200 OK response message
        """
        
        res_body = ''
        # get response message body
        abs_path = f"{os.path.abspath('www')}/{self.request_dic['path']}"
        if abs_path[-1] == '/':
            abs_path += 'index.html'
        with open(abs_path, "r") as file:
            res_body = file.read()

        res_headers = [
            f'Date: {self.get_current_date_time()}',
            f'Content-Type: {self.get_mime_type(abs_path)}',
            f'Content-Length: {self.utf8len(res_body)}',
            f'Connection: close'
            f'Location: http://{self.headers_dic["Host"]}{self.request_dic["path"]}'
        ]

        # get the full response message
        res_msg = self.build_res_msg(200, res_headers, res_body)

        return res_msg

    def res_301(self):
        """ Builds a 301 Moved Permanently response message
        """
        res_body = ''
        res_headers = [
            f'Date: {self.get_current_date_time()}',
            f'Content-Length: {self.utf8len(res_body)}',
            f'Connection: close',
            f'Location: http://{self.headers_dic["Host"]}{self.request_dic["path"]}'
        ]

        # correct the path
        self.request_dic["path"] += '/'

        # get the full response message
        res_msg = self.build_res_msg(301, res_headers)
        
        return res_msg

    def res_404(self):
        """ Builds a 404 Not Found response message
        """
        res_body = self.page_404()
        res_headers = [
            f'Date: {self.get_current_date_time()}',
            f"Content-Type: text/html",
            f'Content-Length: {self.utf8len(res_body)}',
            f'Connection: close'
        ]

        res_msg = self.build_res_msg(404, res_headers, res_body)
        return res_msg

    def res_405(self):
        """ Builds a 405 Method Not Allowed response message
        """
        res_headers = []
        res_msg = self.build_res_msg(405, res_headers)
        return res_msg

    def get_current_date_time(self):
        """Gets the current time 

        Returns:
            A string formatted to the correct format in HTTP date
        """
        return datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %Z")

    def utf8len(self, s):
        """ Gets the length of a string in bytes.
        Ref: https://stackoverflow.com/questions/30686701/python-get-size-of-string-in-bytes

        Args:
            s (string): The string to get the length of

        Returns:
            The length of the given string in bytes
        """
        return len(s.encode('utf-8'))

    def page_404(self):
        # fun :)
        return (r"""
        <html><head><style type=text/css>
        p {    color: red;    
        font-weight: 900;    
        font-size: 20px;    
        font-family: Helvetica, Arial, sans-serif;    
        }
        </style></head>
        <h1> 404 Not Found </h1>
        <body>
        <p>No cap on god fam whatever you're looking for is not here bruh.</p>
        </body>
        </html>
        """)

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
