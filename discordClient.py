import requests
import os
from dotenv import load_dotenv
from dataclasses import dataclass

@dataclass
class DiscordAuthor:
    id: str
    username: str
    global_name: str | None
    
@dataclass
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
        self._last_msg_id = 0
        
        if not os.getenv("DISCORD_TOKEN"):
            raise RuntimeError("DISCORD_TOKEN not set")
        self._HEADERS = {
            "Authorization": os.getenv("DISCORD_TOKEN"),
            "Content-Type": "application/json"}
        
        
    def get_msg(self, channel_id, get_limit=10, url=None):
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


    class API:
        def __init__(self, outer: "DiscordClient"):
            self.outer = outer
        
        def fetch_new_msg(self, channel_id: str, msg_limit: int=10)-> list[DiscordMessage]:
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
            return self.outer.get_msg(channel_id, msg_limit)
        

# Example
if __name__=="__main__":
    app = DiscordClient().API
    msgs = app.fetch_new_msg("Discord channel ID")
    for msg in msgs:
        print(f"{msg.author.username} :", msg.content)