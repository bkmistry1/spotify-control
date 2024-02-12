import discord
from discord.ext import commands

class PersistentViewBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=intents)

    async def setup_hook(self) -> None:
        # self.add_view(PersistentView())
        ...