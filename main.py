import webview
import threading

import bookmanager

app = bookmanager.create_app()

def start_flask():
    app.run()

if __name__ == "__main__":
    # flaskを別スレッドで起動
    threading.Thread(target=start_flask).start()

    # ウインドウ作成
    webview.create_window("Book Manager", "http://127.0.0.1:5000")
    webview.start()