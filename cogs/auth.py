import discord
import asyncio

from discord import app_commands
from discord.ext import commands
from views import PersistentViewBot

from spotifycmds import *
from env_variables import *

class Authentication(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.name = "Authentication"

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.name} cog loaded", flush=True)

    @commands.command(name="sync")
    async def sync(self, ctx) -> None:
        await ctx.send("Syncing")
        try:
            fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        except Exception as e:
            print(e, flush=True)
            
        await ctx.send(f"Synced {len(fmt)} commands")
        return
    
    @app_commands.command(name="auth", description="Authorize with spotify")
    async def spotifyAuthorization(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        authCheck = await findOneFromDb(colName="spotifyTokens", dict={"userId": interaction.user.id})
        if(authCheck is not None):
            await refreshToken(userId=interaction.user.id)
            await interaction.followup.send("Authorization was successfull")
            return

        view = await spotifyGetAuth(interaction=interaction)
        await interaction.followup.send(ephemeral=True, view=view)

        count = 0
        while(count < 120):
            codeCheck: dict = await findOneFromDb(colName="spotifyUsers", dict={"userId": interaction.user.id})
            if("code" in codeCheck.keys()):
                await getUserAccessToken(interaction=interaction, code=codeCheck["code"])
                break
            await asyncio.sleep(3)
            count += 3


        return  
    
    @app_commands.command(name="playback_devices", description="Get list of playback devices")
    async def getListOfPlaybackDevices(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        token = await userTokenById(userId=interaction.user.id)
        playbackDevices = await getPlaybackDevices(token=token)
        print(playbackDevices)
        await interaction.followup.send("Done", ephemeral=True)
        return
    
    @app_commands.command(name="add_song_to_queue", description="Add song to queue")
    async def addToQueue(self, interaction: discord.Interaction, search_term: str):
        await interaction.response.defer(ephemeral=True)
        await searchSong(interaction=interaction, searchTerm=search_term)        
        return
    
    @app_commands.command(name="host", description="Host a spotify queue")
    async def host(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await spotifyHost(interaction)
        return    
    
    @app_commands.command(name="playlists", description="Display your playlists")
    async def playlists(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await getPlaylists(interaction)
        return        
        
async def setup(bot: PersistentViewBot):
    await bot.add_cog(Authentication(bot), guilds=[discord.Object(id=guildId)])