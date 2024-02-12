import discord
from discord import app_commands
from discord.ext import commands

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
        await interaction.response.defer(ephemeral=True, thinking=True)
        return  
        
async def setup(bot):
    await bot.add_cog(Authentication(bot), guilds=[discord.Object(id=1017931589340123268)])