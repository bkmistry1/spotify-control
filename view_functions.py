import discord
import requests

from data.mongoFunctions import *
from spotify_api.custom_queue import *

async def addSongToQueue(spotifyUser, songUri):

    token = await userTokenById(userId=spotifyUser["userId"])

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
