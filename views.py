import discord
from discord.ext import commands
from discord.ui import View, Button, Select

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

    @discord.ui.button(label="Invite", custom_id="host_invite_btn", row=0)
    async def inviteBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        members: list[discord.Member] = interaction.guild.members
        memberList = []
        for member in members:
            memberList.append(discord.SelectOption(label=member.name, value=member.id, description=""))

        selectMenu = spotifyHostInviteSelection(placeholder="Select Members to Invite To Session", options=memberList, min=1, max=len(memberList))
        
        sessionView = spotifyHostSession()
        sessionView.add_item(selectMenu)

        await interaction.followup.send(view=sessionView, ephemeral=True)
        return
    
    @discord.ui.button(label="End Session", custom_id="host_end_session_btn", row=0)
    async def endSession(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        categoryChannel = channel.category
        await channel.delete()
        await categoryChannel.delete()
        await deleteOneFromDb(colName="currentHostSessions", dict={"messageId": interaction.message.id})
        return    
    
    @discord.ui.button(custom_id="host_previous_button", emoji="⏮️", row=1)
    async def previousTrack(self, interaction: discord.Interaction, button: discord.ui.Button):
        host = await findOneFromDb(colName="currentHostSessions", dict={"messageId": interaction.message.id})
        await previous(userId=host["userId"])        
        embed = interaction.message.embeds[0]
        await interaction.response.edit_message(embed=embed)        
        return   

    @discord.ui.button(custom_id="host_play_pause_button", emoji="⏯️", row=1)
    async def playPauseTrack(self, interaction: discord.Interaction, button: discord.ui.Button):
        host = await findOneFromDb(colName="currentHostSessions", dict={"messageId": interaction.message.id})
        await playPause(userId=host["userId"])
        embed = interaction.message.embeds[0]
        await interaction.response.edit_message(embed=embed)
        return
            
    @discord.ui.button(custom_id="host_next_button", emoji="⏭️", row=1)
    async def nextTrack(self, interaction: discord.Interaction, button: discord.ui.Button):
        host = await findOneFromDb(colName="currentHostSessions", dict={"messageId": interaction.message.id})
        await next(userId=host["userId"])
        embed = interaction.message.embeds[0]
        await interaction.response.edit_message(embed=embed)
        return

class spotifyHostSession(View):
    def __init__(self):
        super().__init__()

class spotifyHostInviteSelection(Select):
    def __init__(self, placeholder, options, min, max):
        super().__init__(placeholder=placeholder, options=options, min_values=min, max_values=max)

    async def callback(self, interaction: discord.Interaction):
        
        await interaction.response.defer(ephemeral=True)
        for selection in self.values:                        
            channel = interaction.channel
            categoryChannel = channel.category
            guild = interaction.guild            
            try:
                member = guild.get_member(int(selection))
                await categoryChannel.set_permissions(target=member, read_messages=True, send_messages=True)            
                await channel.set_permissions(target=member, read_messages=True, send_messages=True)
            except Exception as e:
                print(e, flush=True)
                return

        await interaction.followup.send("Done", ephemeral=True)
        return 