# bot.py

import os
import discord
import asyncio

from dotenv import load_dotenv
from views import PersistentViewBot

load_dotenv()

TOKEN=os.getenv("DISCORD_TOKEN")

# intents = discord.Intents.all()
bot = PersistentViewBot()

@bot.event 
async def on_ready():
    print("Bot is Up and Ready!", flush=True)
    await bot.change_presence(activity=discord.Game(name="/help"))

@bot.event
async def load():
    print("loading", flush=True)
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f'cogs.{file[:-3]}')

async def main():
    await load()
    await bot.start(TOKEN)
    
asyncio.run(main())

