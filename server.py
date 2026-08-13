from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class ServerException(Exception):
    """For internal server errors."""
    pass

class case_no_file:
    '''File or directory does not exist.'''
    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))

class  case_existing_file:
    '''Path points directly to a file.'''
    def test(self, handler):
        return os.path.isfile(handler.full_path)

    def act(self, handler):
        handler.handle_file(handler.full_path)

class case_directory_index_file:
    '''Serve index.html page for a directory if it exists.'''
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
               os.path.isfile(self.index_path(handler))

    def act(self, handler):
        handler.handle_file(self.index_path(handler))

class case_directory_no_index_file:
    '''Serve listing for a directory without an index.html page.'''
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
               not os.path.isfile(self.index_path(handler))

    def act(self, handler):
        handler.list_dir(handler.full_path)

class case_always_fail:
    '''Base fallback case if nothing else matched.'''
    def test(self, handler):
        return True

    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))

class RequestHandler(BaseHTTPRequestHandler):

    Cases = [
        case_no_file(),
        case_existing_file(),
        case_directory_index_file(),
        case_directory_no_index_file(),
        case_always_fail()
    ]

    Error_Page = """\
    <html>
    <body>
    <h1>Error accessing {path}</h1>
    <p>{msg}</p>
    </body>
    </html>
    """

    Listing_Page = """\
    <html>
    <body>
    <h2>Directory Listing for {path}</h2>
    <ul>
    {0}
    </ul>
    </body>
    </html>
    """

    def do_GET(self):
        try:
            self.full_path = os.getcwd() + self.path

            # Delegate handling to the first matching case
            for case in self.Cases:
                if case.test(self):
                    case.act(self)
                    break

        except Exception as msg:
            self.handle_error(msg)

    def handle_file(self, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            self.send_content(content)

        except IOError as msg:
            msg = "'{0}' cannot be read : {1}".format(self.path, msg)
            self.handle_error(msg)

    def lis_dir(self, full_path):
        try:
            entries = os.listdir(full_path)
            bullets = ['<li>{0}</li>'.format(e) for e in entries if not e.startwith('.')]
            html_content = self.Listing_Page.format('\n'.join(bullets), path=self.path)
            self.send_content(html_content.encode('utf-8'))
        except OSError as msg:
            msg = "'{0}' cannot be listed: {1}".format(self.path, msg)
            self.handle_error(msg)

    def handle_error(self, msg):
        content = self.Error_Page.format(path=self.path, msg=msg).encode('utf-8')
        self.send_content(content, status=404)

    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

if __name__ == '__main__':
    server_address = ('', 8080)
    server = HTTPServer(server_address,RequestHandler)
    print("Server running on port 8080....")
    server.serve_forever()