import discord
import requests
import asyncio

from data.mongoFunctions import *
from spotify_api.custom_queue import *
from global_variables_functions import *
from spotify_views import *


async def addSongToQueue(spotifyUser, songUri):

    try:
        token = await userTokenById(userId=spotifyUser)
    except Exception as e:
        print(e, flush=True)

    params = {}
    params["uri"] = songUri

    headers = {}
    headers["Authorization"] = "Bearer " + token
    
    url = "https://api.spotify.com/v1/me/player/queue"

    response = requests.post(url=url, params=params, headers=headers)
    
    return        

async def userTokenById(userId):
    tokenInfo = await findOneFromDb(colName="spotifyTokens", dict={"userId": userId})
    token = tokenInfo["token"]["access_token"]
    return token

async def next(userId):
    
    token = await userTokenById(userId=userId)
    url = "https://api.spotify.com/v1/me/player/next"

    headers = {}
    headers["Authorization"] = "Bearer " + token

    requests.post(url=url, headers=headers)
    return

async def previous(userId):
    token = await userTokenById(userId=userId)
    url = "https://api.spotify.com/v1/me/player/previous"

    headers = {}
    headers["Authorization"] = "Bearer " + token

    requests.post(url=url, headers=headers)
    return

async def shuffleList(listToShuffle: list):
    random.shuffle(listToShuffle)
    return listToShuffle

async def shuffle(userId):
    
    token = await userTokenById(userId=userId)
    
    try:
        allSongs = await getSpotifyQueue(token=token, userId=userId)
    except Exception as e:
        print(e)
        return
    if(allSongs == 401):
        return 401
    shuffledSongList = await shuffleSongs(allSongs=allSongs)

    return shuffledSongList

async def playPause(userId):
    token = await userTokenById(userId=userId)

    url = "https://api.spotify.com/v1/me/player/"
    headers = {}
    headers["Authorization"] = "Bearer " + token    

    # determine if paused or playing
    currentlyPlaying = await getCurrentlyPlaying(userId=userId)
    if(currentlyPlaying["is_playing"] is False):
        
        # play call
        url += "play"
        headers["Content-Type"] = "application/json"

    else:
        # pause call
        url += "pause"

    requests.put(url=url, headers=headers)        
    return

async def getCurrentlyPlaying(userId):

    token = await userTokenById(userId=userId)

    headers = {}

    headers["Authorization"] = "Bearer " + token

    url = "https://api.spotify.com/v1/me/player/currently-playing"

    response = requests.get(url=url, headers=headers)
    responseJson = response.json()

    return responseJson

async def getYourPlaylists(userId):

    token = await userTokenById(userId=userId)
    spotifyUserDetails = await getSpotifyUserProfile(userId=userId)
    spotifyUserId = spotifyUserDetails["id"]

    url = "https://api.spotify.com/v1/users/"+ spotifyUserId +"/playlists"

    headers = {}
    
    headers["Authorization"] = "Bearer " + token

    response = requests.get(url=url, headers=headers)
    responseJson = response.json()

    return responseJson

async def getSpotifyUserProfile(userId):
    
    token = await userTokenById(userId=userId)
    url = "https://api.spotify.com/v1/me"

    headers = {}
    headers["Authorization"] = "Bearer " + token


    response = requests.get(url=url, headers=headers)
    if(response.status_code == 401):
        statusCode = await refreshToken(userId=userId)
        if(statusCode == 200):
            response = requests.get(url=url, headers=headers)
        else:
            return
    responseJson = response.json()

    return responseJson

async def addTracksToPlaylist(userId, playlistId, trackUris):

    # check if tracks are already in playlist
    playlistItems = await getPlaylistTracks(userId=userId, playlistId=playlistId)


    playlistUris = []
    for track in playlistItems:
        playlistUris.append(track["track"]["uri"])

    for trackUri in trackUris:
        if(trackUri in playlistUris):
            trackUris.remove(trackUri)

    if(len(trackUris) < 1):        
        return
    
    # end check
    
    token = await userTokenById(userId=userId)

    url = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"

    headers = {}
    headers["Authorization"] = "Bearer " + token

    json = {}

    json["uris"] = trackUris

    response = requests.post(url=url, headers=headers, json=json)
    responseJson = response.json()

    return responseJson

async def getPlaylistTracks(userId, playlistId):
    token = await userTokenById(userId=userId)

    url = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"

    headers = {}
    headers["Authorization"] = "Bearer " + token
    
    params = {}
    params["limit"] = 50

    response = requests.get(url=url, headers=headers, params=params)
    responseJson = response.json()

    return responseJson["items"]

async def getAllPlaylistTracks(userId, playlistId):
    token = await userTokenById(userId=userId)

    url = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"

    headers = {}
    headers["Authorization"] = "Bearer " + token
    
    params = {}
    
    limit = 50
    offset = 0
    params["limit"] = limit    

    trackLength = 50
    allTracks = []

    while(trackLength >= limit):
        await asyncio.sleep(3)
        params["offset"] = offset
        response = requests.get(url=url, headers=headers, params=params)
        responseJson = response.json()
        trackLength = len(responseJson["items"])        
        
        for trackObject in responseJson["items"]:
            if(trackObject["track"] is not None):
                allTracks.append(trackObject["track"])
            else:
                print("None")
        offset += limit

    return allTracks

async def searchSong(interaction: discord.Interaction, searchTerm):

    # find the host queue host Id to get the auth token
    channel = interaction.channel
    
    messages = [message async for message in channel.history(limit=100)]

    spotifyUser = None
    for message in messages:
        if(message.author.name == "spotifyControl" and len(message.embeds)>0):
            embedTitle = message.embeds[0].title
            hostUser = embedTitle.removeprefix("Spotify Host: ")
            spotifyUser = await findOneFromDb(colName="spotifyUsers", dict={"userName": hostUser})
            break

    if(spotifyUser is None):
        await interaction.followup.send("No Queue was found", ephemeral=True)
    
    token = await userTokenById(spotifyUser["userId"])

    params = {}
    params["q"] = searchTerm
    params["type"] = "track"
    params["limit"] = 24

    headers = {}
    headers["Authorization"] = "Bearer " + token

    url = "https://api.spotify.com/v1/search"

    responseCheck = False
    while(responseCheck is not True):
        response = requests.get(url=url, params=params, headers=headers)
        if(response.status_code != 200):
            if(response.reason == "Unauthorized"):
                refreshCheck = await refreshToken(userId=interaction.user.id)
                if(refreshCheck == 200):
                    await interaction.followup.send("Spotify Token was expired. Reauthorized", ephemeral=True)
                    headers["Authorization"] = "Bearer " + token
                    token = await userTokenById(spotifyUser["userId"])
                else:
                    await interaction.followup.send("Failed: Probably expired Token. Tell Bhavin plz.", ephemeral=True)
                    return
        else:
            responseCheck = True
    
    responseJson = response.json()

    listOfSongs = responseJson["tracks"]["items"]

    if(len(listOfSongs) < 1):

        await interaction.followup.send("No tracks were found, try a new search", ephemeral=True)
        return

    trackInfo = {}
    trackSelectOptions = []

    for song in listOfSongs:

        labelString = str(song["name"] + " by ")
        artistString = ""
        for artist in song["artists"]:
            artistString += artist["name"] + ", "
        artistString = artistString[:-2]

        labelString += artistString
        valueString = labelString
        descriptionString = artistString

        labelString = await labelValueCheck(labelValueString=labelString)
        valueString = await labelValueCheck(labelValueString=valueString)

        if(labelString in trackInfo.keys()):
            continue
        trackInfo[labelString] = { 
            "name": song["name"],
            "uri": song["uri"],
            "artists": song["artists"],
        }
        trackSelectOption = await createDiscordSelectOptions(label=labelString, value=valueString, description=descriptionString)
        trackSelectOptions.append(trackSelectOption)

    trackSelectOptionMenu = songSelectList(options=trackSelectOptions, trackInfo=trackInfo, spotifyUser=spotifyUser)
    trackSelectBtn = songSelectButton(selectMenu=trackSelectOptionMenu)
    trackSelectionView = songSelectionView()
    trackSelectionView.add_item(trackSelectOptionMenu)
    trackSelectionView.add_item(trackSelectBtn)

    try:
        await interaction.followup.send(view=trackSelectionView, ephemeral=True)
    except Exception as e:
        print(e)
    
    return
