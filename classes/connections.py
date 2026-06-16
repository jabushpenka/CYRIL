from fastapi import WebSocket

class Connection:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.groups : list[int] = []

    def add(self, group_id : int):
        if not group_id in self.groups:
            self.groups.append(group_id)

    def rem(self, group_id : int):
        self.groups.remove(group_id)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[Connection] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        connection = Connection(websocket)
        self.active_connections.append(connection)

    def disconnect(self, websocket: WebSocket):
        for connection in self.active_connections:
            if connection.websocket == websocket:
                self.active_connections.remove(connection)

    def add_group(self, websocket: WebSocket, group_id : int):
        for connection in self.active_connections:
            if connection.websocket == websocket:
                connection.add(group_id)

    def remove_group(self, websocket: WebSocket, group_id : int):
        for connection in self.active_connections:
            if connection.websocket == websocket:
                connection.rem(group_id)

    async def broadcast(self, group_id: int, message: str):
        for connection in self.active_connections:
            if group_id in connection.groups:
                try:
                    await connection.websocket.send_text(message)
                except Exception as e:
                    print("send failed:", e)