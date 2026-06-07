from fastapi import WebSocket

class Connection:
    def __init__(self, websocket: WebSocket, group_id: str):
        self.websocket = websocket
        self.group_id = group_id

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[Connection] = []

    async def connect(self, websocket: WebSocket, group_id: str):
        await websocket.accept()
        connection = Connection(websocket, group_id)
        self.active_connections.append(connection)

    def disconnect(self, websocket: WebSocket):
        for connection in self.active_connections:
            if connection.websocket == websocket:
                self.active_connections.remove(connection)

    async def broadcast(self, group_id: str, message: str):
        for connection in self.active_connections:
            if connection.group_id == group_id:
                await connection.websocket.send_json(message)
