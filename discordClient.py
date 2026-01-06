import requests
import os
import json
from dotenv import load_dotenv
from dataclasses import dataclass

@dataclass(slots=True)
class DiscordAuthor:
    id: str
    username: str
    global_name: str | None
    
@dataclass(slots=True)
class DiscordMessage:
    msg_id: str
    content: str
    author: DiscordAuthor
    mention_ids: list[str]
    timestamp: str

class DiscordClient:
    def __init__(self):
        load_dotenv()
        self.API = self.API(self)
        self._url = None
        self._last_msg_id = 0
        
        
        if not os.getenv("DISCORD_TOKEN"):
            raise RuntimeError("DISCORD_TOKEN not set")
        self._HEADERS = {
            "Authorization": os.getenv("DISCORD_TOKEN")}
        
        
    def _get_msg(self, channel_id, get_limit=10, url=None):
        if not url:
            url = f'https://discord.com/api/v9/channels/{channel_id}/messages?limit={get_limit}'
        response = requests.get(url, headers=self._HEADERS)
        response.raise_for_status()

        messages = response.json()
        messages.reverse()
        new_messages: list[DiscordMessage] = []
        for msg in messages:
            msg_id = msg["id"]
            
            if self._last_msg_id and int(self._last_msg_id) >= int(msg_id):
                continue
            
            self._last_msg_id = msg_id
            author_data = msg["author"]
            
            if author_data.get("bot", False):
                continue
            
            author = DiscordAuthor(
                id = author_data["id"],
                username = author_data["username"],
                global_name=author_data.get("global_name"))
            
            new_messages.append(DiscordMessage(
                msg_id = msg["id"],
                content = msg["content"],
                author = author,
                mention_ids = [name["id"] for name in msg["mentions"]],
                timestamp = msg["timestamp"]))
            
        return new_messages

    def _send_msg(self, channel_id, message, attachment_path, url=None):
        if not url:
            url = f'https://discord.com/api/v9/channels/{channel_id}/messages'
        
        if attachment_path is None:
            payload = {"content": message or ""}
            response =  requests.post(url, headers=self._HEADERS, json=payload)
            return
        
        if not isinstance(attachment_path, list):
            attachment_path = [attachment_path]
        
        if len(attachment_path)>10: 
            raise ValueError("Discord allows up to 10 attachments per message")
        
        payload_json = {"content": message or ""}
        files = {}
        attachment_handle = []
        try:
            for idx, path in enumerate(attachment_path):
                attachment = open(path, "rb")
                files[f"files[{idx}]"] = (os.path.basename(path), attachment)
                attachment_handle.append(attachment)
            files["payload_json"] = (None, json.dumps(payload_json), "application/json")
            
            response = requests.post(url, headers=self._HEADERS, files=files)
        except Exception as e: print(e)
        finally:
            for file in attachment_handle:
                file.close()

    
    
    class API:
        def __init__(self, outer: "DiscordClient"):
            self.outer = outer
        
        def fetch_msg(self, channel_id: str, msg_limit: int=10)-> list[DiscordMessage]:
            """
            Fetch new messages from a Discord channel.

            Parameters
            ----------
            channel_id : str
                Discord channel ID to fetch messages from.
            msg_limit : int, optional
                Maximum number of messages to fetch per request.

            Returns
            -------
            list[DiscordMessage]
                A list of newly fetched Discord messages. Each message contains:
                - msg_id: Discord message ID
                - content: Message content
                - author: DiscordAuthor object
                    - author.id
                    - author.username
                    - author.global_name
                - mention_ids: List of mentioned user IDs
                - timestamp: ISO 8601 timestamp string
            """
            return self.outer._get_msg(channel_id, msg_limit)
        
        def send_msg(self, channel_id: str, message:str|None=None, attachment_path:str|list[str]|None=None):
            """
            Send message and attachment to the Discord channel.

            Parameters
            ----------
            channel_id : str
                Discord channel ID to Send message or attachment to.
            message : str, optional
                Text content of the message.
            attachment_path : str, list[str], optional
                Path or paths to files to be set as attachment. 
                Supported types include images, PDFs, and other files allowed by discord.
            """
            
            self.outer._send_msg(channel_id, message, attachment_path)
        
        def reset_cursor(self):
            """
            Reset the message cursor used for fetching new messages.
            """
            self.outer._last_msg_id = 0
# Example
if __name__=="__main__":
    app = DiscordClient().API
    discord_id = "Discord channel ID"
    msgs = app.fetch_msg(discord_id)
    for msg in msgs:
        print(f"{msg.author.username} :", msg.content)
    app.send_msg(discord_id, "message", ["filepath1", "filepath2"])
