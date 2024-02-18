# bot.py

import os
import discord
import asyncio

from dotenv import load_dotenv
from views import PersistentViewBot
from spotify_api.playback import *

load_dotenv()

TOKEN=os.getenv("DISCORD_TOKEN")

# intents = discord.Intents.all()
bot = PersistentViewBot()

@bot.event 
async def on_ready():
    print("Bot is Up and Ready!", flush=True)
    await bot.change_presence(activity=discord.Game(name="/help"))
    asyncio.gather(startPlaybackRoutine())

@bot.event
async def load():
    print("loading", flush=True)
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f'cogs.{file[:-3]}')

async def startPlaybackRoutine():
    while(1):
        await asyncio.sleep(5)
        try:
            await getQueue(bot=bot)
        except Exception as e:
            print(e, flush=True)
    

async def main():
    await load()
    await bot.start(TOKEN)
    
asyncio.run(main())

