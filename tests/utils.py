import contextlib
import http.server
import threading


class HttpServerThread(threading.Thread):
    def __init__(self, handler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = http.server.HTTPServer(("localhost", 7777), handler)

    def run(self):
        self.server.serve_forever(poll_interval=0.01)

    def terminate(self):
        self.server.shutdown()
        self.server.server_close()
        self.join()


@contextlib.contextmanager
def http_server(handler):
    server_thread = HttpServerThread(handler, daemon=True)
    server_thread.start()
    try:
        yield server_thread
    finally:
        server_thread.terminate()
