import discord
from discord.ext import commands
from discord.ui import View, Button

from view_functions import *

class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=intents)

    async def setup_hook(self) -> None:
        self.add_view(spotifyHostView())

class authLinkView(View):
    def __init__(self):
        super().__init__()
        self.value = 0

class spotifyAuthBtn(Button):
    def __init__(self, url):
        super().__init__(label="Authorize Link", url=url)

class spotifyHostView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.hostId = None  