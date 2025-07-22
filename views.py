# from typing import Any
import discord
import asyncio

from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput

from view_functions import *
from my_custom_classes import *
from global_variables_functions import *

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
        self.message: discord.Message = None
        self.shuffledSongList: SongNode = None
        self.shuffleTask: asyncio.Task = None
        self.refreshTokenTask: asyncio.Task = None
        self.nextUpTrack: SongNode = None
        self.nextUpQueueTracker = False
        self.locked = False

    async def ownerCheck(self, messageId, userId):
        hostSession = await findOneFromDb(colName="currentHostSessions", dict={"messageId": messageId})
        if(hostSession["userId"] != userId):
            return False
        else:
            return True

    async def lockCheck(self):
        while(self.locked == True):
            await asyncio.sleep(2)
        return

    async def convertTime(self, time):
        millis=time
        millis = int(millis)
        seconds=(millis/1000)%60
        seconds = int(seconds)
        minutes=(millis/(1000*60))%60
        minutes = int(minutes) 

        if(seconds < 10):
            seconds = "0" + str(seconds)

        return str(minutes) + ":" + str(seconds)    

    async def shuffledSongQueue(self, message: discord.Message):
        while(1):
            try:
                await asyncio.sleep(5)

                await self.lockCheck()
                self.locked = True

                count = 0
                
                currentlyPlayingObject = await getCurrentlyPlaying(userId=self.hostId)        
                if("item" not in currentlyPlayingObject.keys()):
                    userTokensValidDict[self.hostId] = False
                    self.locked = False
                    continue
                trackObject = currentlyPlayingObject["item"]
                currentlyPlayingSongNode = SongNode(name=trackObject["name"], uri=trackObject["uri"], artists=trackObject["artists"])                
                currentSongName = await currentlyPlayingSongNode.getSongName()
                currentArtists = await currentlyPlayingSongNode.getArtistsString()
                currentSongName += " by " + currentArtists
                songLength = await self.convertTime(trackObject["duration_ms"])
                progress = await self.convertTime(currentlyPlayingObject["progress_ms"])

                timeLeftPercentage = currentlyPlayingObject["progress_ms"] / trackObject["duration_ms"]

                if(self.nextUpQueueTracker is True and timeLeftPercentage < 0.8):
                    self.nextUpQueueTracker = False
                    self.nextUpTrack = None

                if(timeLeftPercentage > 0.8 and self.nextUpQueueTracker is False and self.shuffledSongList is not None):
                    await addSongToQueue(spotifyUser=self.hostId, songUri=self.shuffledSongList.uri)
                    self.nextUpTrack = self.shuffledSongList
                    self.shuffledSongList = self.shuffledSongList.next
                    self.nextUpQueueTracker = True

                songQueueString = ""
                queue = self.shuffledSongList

                while(count < 24 and queue is not None):
                    
                    songName = await queue.getSongName()
                    artistString = await queue.getArtistsString()
                    queuedBy = await queue.getQueuedBy()

                    tempString = f"{count+1}. {songName} by {artistString}"
                    if(len(songQueueString) + len(tempString) > 1024):
                        break
                    songQueueString += f"{count+1}. {songName} by {artistString}"
                    if(queuedBy is not None):
                        songQueueString += "----" + queuedBy
                    songQueueString += "\n"
                    queue = queue.next
                    count += 1
                    

                embed = message.embeds[0]
                for index, field in enumerate(embed.fields):
                    if(field.name == "Currently Playing"):
                        embed.set_field_at(index=index, name="Currently Playing", value=currentSongName, inline=False)

                    if(field.name == "Progress"):
                        embed.set_field_at(index=index, name="Progress", value=str(progress), inline=True)

                    if(field.name == "Length"):
                        embed.set_field_at(index=index, name="Length", value=str(songLength), inline=True)
                    
                    if(field.name == "Next Up"):
                        nextUpQueueString = ""
                        if(self.nextUpTrack is not None):
                            nextUpName = await self.nextUpTrack.getSongName()
                            nextUpArtistString = await self.nextUpTrack.getArtistsString()
                            queuedBy = await self.nextUpTrack.getQueuedBy()

                            nextUpQueueString = f"1. {nextUpName} by {nextUpArtistString}"                                            
                            if(queuedBy is not None):
                                nextUpQueueString += "----" + queuedBy
                            nextUpQueueString += "\n"
                        else:
                            nextUpQueueString = None
                        embed.set_field_at(index=index, name="Next Up", value=nextUpQueueString, inline=False)

                    if(field.name == "Queue"):
                        if(self.shuffledSongList is None):
                            songQueueString = None
                        embed.set_field_at(index=index, name="Queue", value=songQueueString, inline=False)
                        break
                self.locked = False
                await message.edit(embed=embed, view=self)
            except Exception as e:
                self.locked = False
                print(e, flush=True)

    @discord.ui.button(label="Invite", custom_id="host_invite_btn", row=0)
    async def inviteBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        if(not await self.ownerCheck(messageId=interaction.message.id, userId=interaction.user.id)):
            await interaction.followup.send("You are not allowed to use this command", ephemeral=True)
            return
        
        members: list[discord.Member] = interaction.guild.members
        memberList = []
        for member in members:
            memberList.append(discord.SelectOption(label=member.name, value=member.id, description=""))

        selectMenu = spotifyHostInviteSelection(placeholder="Select Members to Invite To Session", options=memberList, min=1, max=len(memberList))
        
        sessionView = spotifyHostSession()
        sessionView.add_item(selectMenu)

        await interaction.followup.send(view=sessionView, ephemeral=True)
        return
    
    @discord.ui.button(label="End Session", custom_id="host_end_session_btn", style=discord.ButtonStyle.red, row=0)
    async def endSession(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)        

        if(not await self.ownerCheck(messageId=interaction.message.id, userId=interaction.user.id) and interaction.user.id != 173943287080681472):
            await interaction.followup.send("You are not allowed to use this command", ephemeral=True)
            return        
        
        if(self.shuffleTask is not None):
            self.shuffleTask.cancel()
        if(self.refreshTokenTask is not None):
            self.refreshTokenTask.cancel()            
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
        await interaction.response.defer(ephemeral=True)
        message = await interaction.original_response()        
        host = await findOneFromDb(colName="currentHostSessions", dict={"messageId": interaction.message.id})
        await self.lockCheck()
        self.locked = True

        if(self.nextUpTrack is not None):
            self.nextUpTrack = None
        else:
            await addSongToQueue(spotifyUser=self.hostId, songUri=self.shuffledSongList.uri)
            # self.nextUpTrack = self.shuffledSongList
            self.shuffledSongList = self.shuffledSongList.next
        await next(userId=host["userId"])
        embed = interaction.message.embeds[0]
        self.locked = False
        await interaction.response.edit_message(embed=embed)
        return
    
    @discord.ui.button(label="Add To Playlist", custom_id="host_fav_button", row=0)
    async def addToPlaylist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        host = await findOneFromDb(colName="currentHostSessions", dict={"messageId": interaction.message.id})
        userPlaylists = await getYourPlaylists(userId=host["userId"])
        userPlaylistsOptions = []
        playlistCount = 0
        for playlist in userPlaylists["items"]:
            option = discord.SelectOption(label=playlist["name"], value=playlist["id"], description="")
            userPlaylistsOptions.append(option)
            playlistCount += 1
            if(playlistCount == 24):
                break
            
        playlistOptions = playlistSelect(options=userPlaylistsOptions)
        addToPlaylistView = playlistView()
        addToPlaylistView.selectView = playlistOptions
        addToPlaylistView.hostUserId = host["userId"]
        addToPlaylistView.add_item(playlistOptions)
        
        await interaction.followup.send(view=addToPlaylistView, ephemeral=True)
        return   
    
    @discord.ui.button(label="Add Playlist To Queue", custom_id="host_add_playlist_to_queue_button", row=0)
    async def addPlaylistToQueue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        message = await interaction.original_response()
        host = await findOneFromDb(colName="currentHostSessions", dict={"messageId": interaction.message.id})
        userPlaylists = await getYourPlaylists(userId=host["userId"])
        userPlaylistsOptions = []
        playlistCount = 0
        for playlist in userPlaylists["items"]:
            option = discord.SelectOption(label=playlist["name"], value=playlist["id"], description="")
            userPlaylistsOptions.append(option)
            playlistCount += 1
            if(playlistCount == 24):
                break
            
        playlistOptions = queuePlaylistSelect(options=userPlaylistsOptions)
        addToPlaylistView = queuePlaylistView(spotifyHost=self)
        addToPlaylistView.selectView = playlistOptions
        addToPlaylistView.add_item(playlistOptions)
        
        await interaction.followup.send(view=addToPlaylistView, ephemeral=True)
        return   
    
    @discord.ui.button(label="Add Your Playlist To Queue", custom_id="host_add_your_playlist_to_queue_button", row=2)
    async def addUserPlaylistToQueue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        message = await interaction.original_response()
        userPlaylists = await getYourPlaylists(userId=interaction.user.id)

        # if(userPlaylists)

        userPlaylistsOptions = []
        playlistCount = 0
        for playlist in userPlaylists["items"]:
            option = discord.SelectOption(label=playlist["name"], value=playlist["id"], description="")
            userPlaylistsOptions.append(option)
            playlistCount += 1
            if(playlistCount == 24):
                break
            
        playlistOptions = queuePlaylistSelect(options=userPlaylistsOptions)
        addToPlaylistView = queuePlaylistView(spotifyHost=self)
        addToPlaylistView.selectView = playlistOptions
        addToPlaylistView.add_item(playlistOptions)
        
        await interaction.followup.send(view=addToPlaylistView, ephemeral=True)
        return    
    
    # @discord.ui.button(label="Add Playlist by Spotify Link To Queue", custom_id="host_add_playlist_link_to_queue_button", row=2)
    # async def addPlaylistByLinkToQueue(self, interaction: discord.Interaction, button: discord.ui.Button):
    #     spotifyPlaylistLinkModal = PlaylistSearchModal()
    #     await interaction.response.send_modal(spotifyPlaylistLinkModal)
    #     return    
    
    @discord.ui.button(label="Clear Queue", custom_id="host_clear_queue_button", style=discord.ButtonStyle.red, row=2)
    async def clearSpotifyQueue(self, interaction: discord.Interaction, button: discord.ui.Button):
        # spotifyPlaylistLinkModal = PlaylistSearchModal()
        # await interaction.response.send_modal(spotifyPlaylistLinkModal)
        await interaction.response.defer(ephemeral=True)

        if(self.hostId is None or self.hostId != interaction.user.id):
            message: discord.Message = await interaction.followup.send("Only the host can use this button", ephemeral=True)
            await asyncio.sleep(3)
            await message.delete()
            return

        self.shuffledSongList = None
        message: discord.Message = await interaction.followup.send("Queue Cleared", ephemeral=True)
        await asyncio.sleep(3)
        await message.delete()
        return       

    @discord.ui.button(label="Add Song From Queue To Top", custom_id="host_add_song_to_top_of_queue_button", row=0)
    async def addSongToTopOfQueue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        message = await interaction.original_response()

        await self.lockCheck()
        self.locked = True

        if(self.shuffledSongList is None):
            await interaction.followup.send("There is no music queued", ephemeral=True)
            return
                
        options = []
        allOptionsNodeHead = SelectOptionsNode(next=None, previous=None, options=None)
        optionsDict = {}

        songNode = self.shuffledSongList

        while(songNode.queuedBy is not None):
            songNode = songNode.next

        currentNode = allOptionsNodeHead

        while(songNode is not None):
            options.append(discord.SelectOption(label=songNode.name, value=songNode.uri))
            if(songNode.uri not in optionsDict.keys()):
                optionsDict[songNode.uri] = songNode
            if(len(options) == 24):
                selectionSongsSelectMenu = SelectSongSelection(min_values=1, max_values=len(options), options=options)
                currentNode.options = selectionSongsSelectMenu
                tempNode = SelectOptionsNode(next=None, previous=currentNode, options=None)
                currentNode.next = tempNode
                currentNode = currentNode.next
                # allOptions.append(selectionSongsSelectMenu)
                options = []

            songNode = songNode.next

        if(len(options) > 0):
            selectionSongsSelectMenu = SelectSongSelection(min_values=1, max_values=len(options), options=options)
            currentNode.options = selectionSongsSelectMenu
            tempNode = SelectOptionsNode(next=None, previous=currentNode, options=None)
            currentNode.next = tempNode
            currentNode = currentNode.next
            # allOptions.append(selectionSongsSelectMenu)
            options = []

        allOptionsNodeHead.previous = currentNode.previous
        currentNode.previous.next = allOptionsNodeHead
        
        queueSongSelectView = SelectSongFromQueue(hostView=self, selectedOption=allOptionsNodeHead, optionsDict=optionsDict)
        queueSongSelectView.add_item(allOptionsNodeHead.options)

        self.locked = False

        await interaction.followup.send(view=queueSongSelectView, ephemeral=True)
        return        

    @discord.ui.button(custom_id="host_shuffle_songs_button", emoji="🔀", row=1)
    async def shuffleTracks(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        message = await interaction.original_response()

        await self.lockCheck()
        self.locked = True

        currentNode = self.shuffledSongList

        songNodeList = []
        priorityNodeList: list[SongNode] = []
        while(currentNode is not None):
            if(currentNode.queuedBy is None):
                songNodeList.append(currentNode)
            else:
                priorityNodeList.append(currentNode)
            currentNode = currentNode.next

        songNodeList: list[SongNode] = await shuffleList(listToShuffle=songNodeList)
        songNodeList = priorityNodeList + songNodeList

        headNode = SongNode(name=None, uri=None, artists=None)
        currentNode = headNode

        for node in songNodeList:
            currentNode.next = node
            currentNode = currentNode.next

        currentNode.next = None

        self.shuffledSongList = headNode.next
        self.locked = False
        return    

    @discord.ui.button(label="Search for Song", custom_id="host_search_for_songbutton", style=discord.ButtonStyle.green, row=2)
    async def searchForSongToAddToQueue(self, interaction: discord.Interaction, button: discord.ui.Button):
        searchModal = SongSearchModal()
        try:
            await interaction.response.send_modal(searchModal)
        except Exception as e:
            print(e, flush=True)
        return         

class SongSearchModal(Modal, title="Spotify Search Modal"):
    searchTerm = TextInput(label="Search Term", placeholder="Enter text to search for")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message = await interaction.original_response()
        
        # embed = discord.Embed(title="Modal Response")
        searchTerm = self.searchTerm.value
        
        await searchSong(interaction=interaction, searchTerm=searchTerm)
        # await interaction.response.send_message(embeds=[embed])

class PlaylistSearchModal(Modal, title="Spotify Playlist Search Modal"):
    searchTerm = TextInput(label="Search Term", placeholder="Enter Public spotify playlist link")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message = await interaction.original_response()
        view: spotifyHostView = await getViewFromDict(channelId=interaction.channel.id)
        searchTerm = self.searchTerm.value

        searchTerm = searchTerm.split("?")
        searchTerm = searchTerm[0].split("/")

        spotifyPlaylistId = searchTerm[len(searchTerm)-1]
        playlistTracks = await getAllPlaylistTracks(userId=view.hostId, playlistId=spotifyPlaylistId)
        playlistTracks = await shuffleList(listToShuffle=playlistTracks)

        await view.lockCheck()
        view.locked = True

        songNodeHead = SongNode(name=None, uri=None, artists=None)
        currentNode = songNodeHead
        for track in playlistTracks:
            songNode = SongNode(name=track["name"], uri=track["uri"], artists=track["artists"])
            currentNode.next = songNode
            currentNode = currentNode.next

        currentNode = view.shuffledSongList
        if(currentNode is None):
            view.shuffledSongList = songNodeHead.next
        else:
            while(currentNode.next is not None):
                currentNode = currentNode.next

            currentNode.next = songNodeHead.next

        view.locked = False

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
    

class playlistView(View):
    def __init__(self):
        super().__init__(timeout=None)      

        self.selectView: playlistSelect = None
        self.hostUserId = None

    @discord.ui.button(label="Submit", custom_id="playlistview_submit_btn", row=1)
    async def submitTrack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        playlistId = self.selectView.selectedPlaylist        
        currentlyPlaying = await getCurrentlyPlaying(userId=self.hostUserId)
        trackUris = []
        trackUri = currentlyPlaying["item"]["uri"]
        trackUris.append(trackUri)        
        await addTracksToPlaylist(userId=self.hostUserId, playlistId=playlistId, trackUris=trackUris)
        await msg.edit(content="Done", view=None)
        return

    @discord.ui.button(label="Cancel", custom_id="playlistview_cancel_btn", row=1)      
    async def cancelBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        await msg.delete()
        return

class playlistSelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="Select Playlist to Add Track To", min_values=1, max_values=1, options=options)
        
        self.selectedPlaylist = None

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        self.selectedPlaylist = self.values[0]
        await msg.edit(content=self.selectedPlaylist)
        return 
    

# view for adding playlist to queue
class queuePlaylistView(View):
    def __init__(self, spotifyHost):
        super().__init__(timeout=None)      

        self.spotifyHost: spotifyHostView = spotifyHost
        self.selectView: queuePlaylistSelect = None

    @discord.ui.button(label="Submit", custom_id="queue_playlist_select_submit_btn", row=1)
    async def submitPlaylist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        await msg.edit(content="Adding Playlist", view=None)

        playlistTracks = await getAllPlaylistTracks(self.spotifyHost.hostId, playlistId=self.selectView.selectedPlaylistId)        
        playlistTracks = await shuffleList(listToShuffle=playlistTracks)

        songNodeHead = SongNode(name=None, uri=None, artists=None)
        currentNode = songNodeHead
        for track in playlistTracks:
            songNode = SongNode(name=track["name"], uri=track["uri"], artists=track["artists"])
            currentNode.next = songNode
            currentNode = currentNode.next

        currentNode = self.spotifyHost.shuffledSongList
        if(currentNode is None):
            self.spotifyHost.shuffledSongList = songNodeHead.next
        else:
            while(currentNode.next is not None):
                currentNode = currentNode.next

            currentNode.next = songNodeHead.next

        if(self.spotifyHost.shuffleTask is not None):
            self.spotifyHost.shuffleTask.cancel()
        task = asyncio.create_task(self.spotifyHost.shuffledSongQueue(message=self.spotifyHost.message))
        self.spotifyHost.shuffleTask = task

        await msg.edit(content="Done", view=None)
        await msg.delete()
        return

    @discord.ui.button(label="Cancel", custom_id="queue_playlist_select_cancel_btn", row=1)      
    async def cancelBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        await msg.delete()
        return

class queuePlaylistSelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="Select Playlist to Add to Queue", min_values=1, max_values=1, options=options)
        
        self.selectedPlaylistName = None
        self.selectedPlaylistId = None

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        self.selectedPlaylistId = self.values[0]
        for option in self.options:
            if(option.value == self.selectedPlaylistId):
                self.selectedPlaylistName = option.label
                break

        await msg.edit(content="You Selected: " + self.selectedPlaylistName)
        return 
    

class SelectSongFromQueue(View):
    def __init__(self, hostView, selectedOption, optionsDict):
        super().__init__(timeout=180)

        self.selectedOption: SelectOptionsNode = selectedOption
        self.hostView: spotifyHostView = hostView
        self.optionsDict = optionsDict

    @discord.ui.button(label="Previous Page", custom_id="previous_next_btn", row=2)      
    async def previousBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()

        self.remove_item(self.selectedOption.options)
        self.add_item(self.selectedOption.previous.options)
        self.selectedOption = self.selectedOption.previous

        await msg.edit(view=self)

        return
    
    @discord.ui.button(label="Next Page", custom_id="select_next_btn", row=2)      
    async def nextBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()

        self.remove_item(self.selectedOption.options)
        self.add_item(self.selectedOption.next.options)
        self.selectedOption = self.selectedOption.next

        await msg.edit(view=self)

        return

    @discord.ui.button(label="Submit", custom_id="select_song_submit_btn", row=1)      
    async def submitBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()

        selectMenu: SelectSongSelection = self.selectedOption.options
        

        for uri in selectMenu.selectedSongs:
            headNode = SongNode(name=None, uri=None, artists=None)
            headNode.next = self.hostView.shuffledSongList
            currentNode = headNode
            while(currentNode.next.uri != uri):
                currentNode = currentNode.next
            currentNode.next = currentNode.next.next
        
        headSongNode = SongNode(name=None, uri=None, artists=None)
        currentNode = headSongNode
        
        for uri in selectMenu.selectedSongs:
            currentNode.next = self.optionsDict[uri]            
            currentNode = currentNode.next
            currentNode.queuedBy = interaction.user.name

        tailNode = currentNode                

        songListHeadNode = SongNode(name=interaction.user.name, uri=None, artists=None)
        currentNode = songListHeadNode
        currentNode.next = self.hostView.shuffledSongList

        while(currentNode.next.queuedBy is not None):
            currentNode = currentNode.next

        tempNode = currentNode.next
        currentNode.next = headSongNode.next
        tailNode.next = tempNode 

        self.hostView.shuffledSongList = songListHeadNode.next
        
        
        await msg.delete()
        return
    
    @discord.ui.button(label="Cancel", custom_id="select_song_cancel_btn", row=1)      
    async def cancelBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.original_response()
        await msg.delete()
        return    

    
class SelectSongSelection(Select):
    def __init__(self, min_values, max_values, options):
        super().__init__(
            custom_id="Select_Song_From_Queue", 
            placeholder="Select Songs To Add To Top Of Queue", 
            min_values=min_values, 
            max_values=max_values, 
            options=options
        )

        self.selectedSongs = []

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message = await interaction.original_response()

        selectedValuesString = ""
        for value in self.values:
            self.selectedSongs.append(value)
        
        for song in self.selectedSongs:
            selectedValuesString += song + "\n"
        
        await message.edit(content=selectedValuesString)
        return 