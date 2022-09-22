#  coding: utf-8 
import socketserver
import os
import mimetypes
import datetime

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

    status_codes = {
        200: "OK",
        301: "Permanently Moved",
        404: "Not Found",
        405: "Method Not Allowed"
    }
    webFolder = './www'

    def handle(self):
        self.data = self.request.recv(1024).decode("utf-8").strip()
        print ("Got a request of: %s\n" % self.data)

        lines = self.data.splitlines()
        reqMethod, self.path, self.HTTP_ver = str(lines[0]).split(' ')
        resMessage = ''
        if not self.is_valid_method(reqMethod):
            resMessage = self._405()
        elif self.check_path():
            resMessage = self._301()
        elif not self.path_exists():
            resMessage = self._404()
        else:
            resMessage = self._200()
        
        self.request.sendall(bytearray(resMessage,'utf-8'))

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

    def _405(self):
        resMessage = ''
        status = f'{self.HTTP_ver} 405 {self.status_codes[405]}\r\n'
        resMessage += status + '\r\n'
        return resMessage

    def _404(self):
        resMessage = ''
        status = f'{self.HTTP_ver} 404 {self.status_codes[404]}\r\n'
        
        resBody = self.page_404()
        resHeaders = [
            f'Date: {self.get_current_date_time()}',
            f'Content-Type: text/html',
            f'Content-Length: {self.utf8len(resBody)}',
            f'Connection: close',
            f'Location: http://{self.server.server_address[0]}:{self.server.server_address[1]}{self.path}'
        ]
        resMessage += status + '\r\n'.join(resHeaders) + '\r\n\r\n' + resBody

        return resMessage

    def _301(self):
        resMessage = ''
        status = f'{self.HTTP_ver} 301 {self.status_codes[301]}\r\n'
        resBody = ''
        print("the correct path is " + f'Location: http://{self.server.server_address[0]}:{self.server.server_address[1]}{self.path}/')
        resHeaders = [
            f'Date: {self.get_current_date_time()}',
            f'Content-Type: {self.get_mime_type(self.path)}',
            f'Content-Length: {self.utf8len(resBody)}',
            f'Connection: close',
            f'Location: http://{self.server.server_address[0]}:{self.server.server_address[1]}{self.path}/'
        ]
        resMessage += status + '\r\n'.join(resHeaders) + '\r\n\r\n'


        return resMessage

    def _200(self):
        resMessage = ''
        status = f'{self.HTTP_ver} 200 {self.status_codes[200]}\r\n'
        resBody = ''
        absPath = f"{self.webFolder}{self.path}"
        if absPath[-1] == '/':
            absPath += 'index.html'
        with open(absPath, "r") as file:
            resBody = file.read()
        resHeaders = [
            f'Date: {self.get_current_date_time()}',
            f'Content-Type: {self.get_mime_type(absPath)}',
            f'Content-Length: {self.utf8len(resBody)}',
            f'Connection: close',
            f'Location: http://{self.server.server_address[0]}:{self.server.server_address[1]}{self.path}'
        ]
        resMessage += status + '\r\n'.join(resHeaders) + '\r\n\r\n' + resBody
        

        return resMessage

    def check_path(self):
        pathToCheck = f"{self.webFolder}{self.path}"
        # check that the path is not a file, and that if its missing a slash at the end, if its an existing directory
        return pathToCheck[-1] != '/' and not os.path.isfile(pathToCheck.split('/')[-1]) and os.path.exists(pathToCheck+'/')

    def path_exists(self):
        # normalize path to prevent directory attacks
        pathToCheck = f"{self.webFolder}{os.path.normpath(self.path)}"
        return os.path.exists(pathToCheck)
    
    def is_valid_method(self, reqMethod: str):
        validMethods = [
            'GET'
        ]
        return reqMethod in validMethods

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