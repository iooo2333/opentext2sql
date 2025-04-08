import uvicorn
import time
import os
import http.server
import socketserver
import webbrowser
import time

from .service.app import app

# 启动 FastAPI 后端
def start_backend():
    uvicorn.run(app, host="127.0.0.1", port=8000)

def open_frontend():

    current_directory = os.path.dirname(os.path.abspath(__file__))
    build_directory = os.path.join(current_directory, 'build')
    PORT = 3000

    class SPARequestHandler(http.server.SimpleHTTPRequestHandler):
        # 指定静态文件根目录，不切换工作目录
        def translate_path(self, path):
            # 复用原有方法，但修改根目录为 build_directory
            path = http.server.SimpleHTTPRequestHandler.translate_path(self, path)
            # 将 build_directory 替换默认的工作目录
            relpath = os.path.relpath(path, os.getcwd())
            return os.path.join(build_directory, relpath)
        
        def send_error(self, code, message=None, explain=None):
            # 如果资源不存在则返回 index.html，适用于前端路由
            if code == 404:
                self.path = '/index.html'
                return self.do_GET()
            else:
                return http.server.SimpleHTTPRequestHandler.send_error(self, code, message, explain)

    with socketserver.TCPServer(("", PORT), SPARequestHandler) as httpd:
        print(f"Serving React app on http://localhost:{PORT}")
        httpd.serve_forever()

def start():
    import threading
    # # 在一个线程中启动 FastAPI 后端
    threading.Thread(target=start_backend).start()
    # # 暂停一下，确保后端已启动
    time.sleep(2)
    # 打开前端页面
    open_frontend()
