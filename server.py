#  coding: utf-8 
import socketserver
import os
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
    serverName = 'Python'

    def handle(self):
        self.data = self.request.recv(1024).decode("utf-8").strip()
        print ("Got a request of: %s\n" % self.data)

        lines = self.data.splitlines()
        # get the request line (e.g. GET / HTTP/1.1)
        reqMethod, self.path, self.HTTP_ver = str(lines[0]).split(' ')

        self.reqHeadersDic = {}
        # get the request headers
        try:
            lines = lines[0:lines.index('')]        # formats lines to only include the request and its headers, ignores the body
        except ValueError as e:
            lines                                   # there is no body, just the request and headers
        # get the headers and add it to a dictionary
        for line in lines[1:]:
            header, val = line.split(': ')
            self.reqHeadersDic[header] = val


        # get our response message, according to the conditions
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
        valid_mime_types = {
            "css": "text/css",
            "html": "text/html",
        }
        file = path.split('/')[-1]
        fileType = file.split('.')[-1]
        try:
            mimetype = valid_mime_types[fileType]
        except:
            # default to plain text if file type not found in valid mimetypes
            mimetype = "text/plain"
        return mimetype

    def res_message_builder(self, statusCode, resBody, mimeType, addResHeaders=[]):
        """ Builds a HTTP response message accordingly

        Args:
            statusCode (int): An integer of the status code to be responded back with 
            resBody (str): The response entity body to be responded back with 
            mimeType(str): The mimetype to be used in the Content-Type response header
            addResHeaders(list): Any additional response headers that should be responded back with

        Returns:
            resMessage(str): The HTTP response message
        """
        status = f'{self.HTTP_ver} {statusCode} {self.status_codes[statusCode]}\r\n'

        # create general headers and response headers
        connVal = 'close'
        if 'Connection' in self.reqHeadersDic:
            connVal = self.reqHeadersDic["Connection"]
        resHeaders = [
            f'Date: {self.get_current_date_time()}',
            f'Server: {self.serverName}',
            f'Content-Type: {mimeType}',
            f'Content-Length: {self.utf8len(resBody)}',
            f'Connection: {connVal}'
        ]
        resHeaders.extend(addResHeaders)            # add any addition response headers; changes according to the type of response

        resMessage = status + '\r\n'.join(resHeaders) + '\r\n\r\n' + resBody

        return resMessage

    def _405(self):
        """Builds a 405 Method Not Allowed response message

        Returns:
            The 405 response message
        """
        resBody = ''
        resMessage = self.res_message_builder(405, resBody, self.get_mime_type(self.path))

        return resMessage

    def _404(self):
        """Builds a 404 Not Found response message

        Returns:
            The 404 response message
        """
        resBody = self.page_404()
        resMessage = self.res_message_builder(404, resBody, "text/html")

        return resMessage

    def _301(self):
        """Builds a 301 Moved Permanently response message

        Returns:
            The 301 response message
        """
        resHeaders = [
            f'Location: http://{self.server.server_address[0]}:{self.server.server_address[1]}{self.path}/'
        ]
        resBody = ''
        resMessage = self.res_message_builder(301, resBody, self.get_mime_type(self.path), resHeaders)

        return resMessage

    def _200(self):
        """Builds a 200 OK response message

        Returns:
            The 200 response message
        """

        # get the body to be responded back with (in this case html or css)
        resBody = ''
        absPath = f"{self.webFolder}{self.path}"
        if absPath[-1] == '/':
            absPath += 'index.html'
        with open(absPath, "r") as file:
            resBody = file.read()

        resMessage = self.res_message_builder(200, resBody, self.get_mime_type(absPath))

        return resMessage

    def check_path(self):
        """Checks the requested path as to whether or not it has an ending slash,
        and whether it exists or not.

        Returns:
            True if it passes the check
        """
        pathToCheck = f"{self.webFolder}{self.path}"
        # check that the path is not a file, and that if its missing a slash at the end, if its an existing directory
        return pathToCheck[-1] != '/' and not os.path.isfile(pathToCheck.split('/')[-1]) and os.path.exists(pathToCheck+'/')

    def path_exists(self):
        """Checks if the requested path exists

        Returns:
            True if it exists
        """
        # normalize path to prevent directory attacks
        pathToCheck = f"{self.webFolder}{os.path.normpath(self.path)}"
        return os.path.exists(pathToCheck)
    
    def is_valid_method(self, reqMethod: str):
        """Checks if the requested method is valid

        Args:
            reqMethod (str): The requested method

        Returns:
            True if the method is valid
        """
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