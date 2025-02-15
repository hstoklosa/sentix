# from tenacity import (
#     before_sleep_log,
#     retry,
#     stop_after_attempt,
#     wait_exponential,
# )

import websocket

API_KEY = "3d97f7319b028d1590e25f2b2f4fe544cd70bb64e9f23fc53e0bbd7affab4b93"

class TreeNews():
    """Fetch news from the TreeOfAlpha provider."""

    def __init__(self):
        self.wss = "wss://news.treeofalpha.com/ws"
        self._socket = None

    def connect(self) -> None:
        if self._socket is None:
            self._socket = websocket.WebSocketApp(
                self.wss,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
        
        self._socket.run_forever()

    def on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        print(f"Received: {message}")

    def on_error(self, ws: websocket.WebSocketApp, error: str) -> None:
        print(error)

    def on_close(self, ws: websocket.WebSocketApp, close_status_code: int, close_msg: str) -> None:
        print("### closed ###")

    def on_open(self, ws: websocket.WebSocketApp) -> None:
        ws.send(f"login {API_KEY}")

    def format_news(self):
        return


if __name__ == "__main__":
    tree_news = TreeNews()
    tree_news.connect()