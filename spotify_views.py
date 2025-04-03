import discord
import asyncio


from discord.ui import View, Select, Button
from data.mongoFunctions import *
from view_functions import *
from views import *
from my_custom_classes import *


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
            self.selectedSongs[songSelected] = self.trackInfo[songSelected]
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
        
        for song in self.selectMenu.selectedSongs.keys():
            hostSession = await findOneFromDb(colName="currentHostSessions", dict={"channelId": str(interaction.channel.id)})
            message = await interaction.channel.fetch_message(int(hostSession["messageId"]))
            view: spotifyHostView  = await View.from_message(message=message)

            newSongNode = SongNode(name=None, uri=song["uri"])
            songNodeList: list[SongNode] = view.shuffledSongList

            headNode = SongNode(name=None, uri=None, artists=None)
            headNode.next = songNodeList[0]
            currentNode = headNode

            for songNode in songNodeList:
                if(songNode.next.queuedBy is None):
                    tempNode = currentNode.next
                    currentNode.next = newSongNode
                    newSongNode.next = tempNode
                    break
                else:
                    continue

            view.shuffledSongList = headNode.next                    

            await asyncio.sleep(1)
        await msg.edit(content="Done", view=None)
        return 



