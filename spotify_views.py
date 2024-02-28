import discord
import asyncio


from discord.ui import View, Select, Button
from data.mongoFunctions import *
from view_functions import *


class songSelectionView(View):
    def __init__(self):
        super().__init__()


class songSelectList(Select):
    def __init__(self, options, trackInfo, spotifyUser) -> None:
        super().__init__(placeholder="Select at least 1", options=options, min_values=1, max_values=len(options))
        self.trackInfo = trackInfo
        self.selectedUri = []
        self.spotifyUser = spotifyUser

    async def callback(self, interaction: discord.Interaction):
        songSelectionString = "\n"
        self.selectedUri = []
        for index, songSelected in enumerate(self.values):
            self.selectedUri.append(self.trackInfo[songSelected])
            songSelectionString += str(index) + ". " + songSelected + "\n"
        await interaction.response.edit_message(content="Selected: " + songSelectionString)
        return
    
class songSelectButton(Button):
    def __init__(self, selectMenu):
        super().__init__(label="Submit", custom_id="songSelect_submit_button")
        self.selectMenu: songSelectList = selectMenu

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        songsAdded = 0
        await msg.edit(content="Added: " + str(songsAdded), view=None)
        for songUri in self.selectMenu.selectedUri:
            await addSongToQueue(spotifyUser=self.selectMenu.spotifyUser, songUri=songUri)            
            songsAdded += 1
            await msg.edit(content="Added: " + str(songsAdded), view=None)
            await asyncio.sleep(1)
        await msg.edit(content="Done", view=None)
        return 

