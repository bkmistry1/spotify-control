import discord
import requests

from discord.ui import View, Select, Button
from data.mongoFunctions import *
from view_functions import *


class songSelectionView(View):
    def __init__(self):
        super().__init__()


class songSelectList(Select):
    def __init__(self, options, trackInfo, spotifyUser) -> None:
        super().__init__(options=options, min_values=1, max_values=1)
        self.trackInfo = trackInfo
        self.selectedUri = None
        self.spotifyUser = spotifyUser

    async def callback(self, interaction: discord.Interaction):
        self.selectedUri = self.trackInfo[self.values[0]]
        await interaction.response.edit_message(content="Selected: " + self.values[0])
        return
    
class songSelectButton(Button):
    def __init__(self, selectMenu):
        super().__init__(label="Submit", custom_id="songSelect_submit_button")
        self.selectMenu: songSelectList = selectMenu

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        await addSongToQueue(self.selectMenu.spotifyUser, self.selectMenu.selectedUri)
        await msg.edit(content="Done", view=None)
        return 

