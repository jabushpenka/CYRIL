class MyUpdate:
    def __init__(self, messenger_id : int, chat_id_in_messenger : int, message_id_in_chat : int, text : str, fromuser : str):
        self.messenger_id = messenger_id
        self.chat_id_in_messenger = chat_id_in_messenger
        self.message_id_in_chat = message_id_in_chat
        self.text = text
        self.fromuser = fromuser