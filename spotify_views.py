import discord
import asyncio


from discord.ui import View, Select, Button
from data.mongoFunctions import *
# from view_functions import *
# from views import *
from my_custom_classes import *
from global_variables_functions import *


class songSelectionView(View):
    def __init__(self):
        super().__init__()


class songSelectList(Select):
    def __init__(self, options, trackInfo, spotifyUser) -> None:
        super().__init__(placeholder="Select at least 1", options=options, min_values=1, max_values=len(options))
        self.trackInfo = trackInfo
        self.selectedSongs = {}
        self.spotifyUser = spotifyUser

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        songSelectionString = "\n"
        self.selectedSongs = {}

        embed = discord.Embed(
            title="Song Selection",
            description="List of Songs Selected",
            color=discord.Color.dark_green()
        )        

        for index, songSelected in enumerate(self.values):
            self.selectedSongs[songSelected] = self.trackInfo[songSelected]["uri"]
            songSelectionString += str(index) + ". " + songSelected + "\n"
        
        embed.add_field(name="Songs", value=songSelectionString, inline=False)

        # await msg.edit(content="Selected: " + songSelectionString)
        await msg.edit(embed=embed)
        return
    
class songSelectButton(Button):
    def __init__(self, selectMenu):
        super().__init__(label="Submit", custom_id="songSelect_submit_button")
        self.selectMenu: songSelectList = selectMenu

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()        
        view = await getViewFromDict(interaction.channel.id)

        newSongNodeList = SongNode(name=None, uri=None, artists=None)
        currentNode = newSongNodeList
        for song in self.selectMenu.selectedSongs.keys():            
            newSongNode = SongNode(
                name=self.selectMenu.trackInfo[song]["name"], 
                uri=self.selectMenu.trackInfo[song]["uri"], 
                artists=self.selectMenu.trackInfo[song]["artists"]
            )

            newSongNode.queuedBy = interaction.user.name
            currentNode.next = newSongNode
            currentNode = currentNode.next

        newSongNodeListTail = currentNode
        songNodeList = view.shuffledSongList        
        headNode = SongNode(name=None, uri=None, artists=None)

        if(songNodeList is not None):    
            headNode.next = songNodeList
            currentNode = headNode

            while(currentNode.next is not None and currentNode.next.queuedBy is not None):
                currentNode = currentNode.next

            tempNode = currentNode.next    
            currentNode.next = newSongNodeList.next
            newSongNodeListTail.next = tempNode
        
        else:
            headNode.next = newSongNodeList.next

        view.shuffledSongList = headNode.next

        await asyncio.sleep(1)

        await msg.edit(content="Done", view=None)
        await asyncio.sleep(3)
        await msg.delete()
        return 



