import requests
import random
import string
import base64

from env_variables import *
from views import *
from data.mongoFunctions import *
from spotify_views import *


async def requestAuthToken():
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {}
    params["grant_type"] = "client_credentials"
    params["client_id"] = clientId
    params["client_secret"] = clientSecret

    response = requests.post(url=url, headers=headers, params=params)
    responseJson = response.json()

    return responseJson["access_token"]

async def userToken(interaction: discord.Interaction):
    tokenInfo = await findOneFromDb(colName="spotifyTokens", dict={"userId": interaction.user.id})
    token = tokenInfo["token"]["access_token"]

    return token    

async def getPlaybackDevices(token):
    url = "https://api.spotify.com/v1/me/player/devices"
    headers = {"Authorization": "Bearer " + token}
    params = {}

    response = requests.get(url=url, headers=headers, params=params)
    responseJson = response.json()

    print(responseJson)
    return

async def spotifyGetAuth(interaction: discord.Interaction):
    redirect_uri = redirectUrl

    n = 16

    state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))
    scope = "user-read-private%20user-read-email%20user-read-playback-state%20user-modify-playback-state"

    await insertIntoCollection(colName="spotifyUsers", mydict={"userId": interaction.user.id, "userName": interaction.user.name, "state": state})

    params = {}
    params["response_type"] = "code"
    params["client_id"] = clientId
    params["scope"] = scope
    params["redirect_uri"] = redirect_uri
    params["state"] = state

    url = "https://accounts.spotify.com/authorize?response_type=code&client_id="+clientId+"&scope="+scope+"&redirect_uri="+redirect_uri+"&state="+state+""

    authBtn = spotifyAuthBtn(url=url)
    authView = authLinkView()

    authView.add_item(authBtn)

    return authView

async def getUserAccessToken(interaction: discord.Interaction, code):

    headers = {}
    stringToEncode: str = clientId + ":" + clientSecret
    encodedClientIdSecret = base64.b64encode(stringToEncode.encode("ascii"))
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    headers["Authorization"] = "Basic " + encodedClientIdSecret.decode("ascii")

    params = {}
    params["code"] = code
    params["redirect_uri"] = redirectUrl
    params["grant_type"] = "authorization_code"

    url = "https://accounts.spotify.com/api/token"
    response = requests.post(url=url, params=params, headers=headers)

    responseJson = response.json()

    print(responseJson)

    await insertIntoCollection(colName="spotifyTokens", mydict={"userId": interaction.user.id, "token": responseJson})

    return

async def addSongToQueue(interaction: discord.Interaction, songUri):

    
    token = await userToken(interaction=interaction)

    params = {}
    params["uri"] = songUri

    headers = {}
    headers["Authorization"] = "Bearer " + token
    
    url = "https://api.spotify.com/v1/me/player/queue"

    response = requests.post(url=url, params=params, headers=headers)
    
    return

async def searchSong(interaction: discord.Interaction, searchTerm):

    token = await userToken(interaction=interaction)

    print('oh')

    params = {}
    params["q"] = searchTerm
    params["type"] = "track"
    params["limit"] = 5

    headers = {}
    headers["Authorization"] = "Bearer " + token

    url = "https://api.spotify.com/v1/search"

    response = requests.get(url=url, params=params, headers=headers)
    responseJson = response.json()

    listOfSongs = responseJson["tracks"]["items"]

    trackInfo = {}
    trackSelectOptions = []
    print("unchi")
    for song in listOfSongs:
        trackInfo[song["name"] + " by " + song["artists"][0]["name"]] = song["uri"]
        trackSelectOption = await createDiscordSelectOptions(label=str(song["name"] + " by " + song["artists"][0]["name"]), value=str(song["name"] + " by " + song["artists"][0]["name"]), description=str(song["artists"][0]["name"]))
        trackSelectOptions.append(trackSelectOption)
        # await addSongToQueue(interaction=interaction, songUri=song["uri"])
    
    print(trackSelectOptions)
    trackSelectOptionMenu = songSelectList(options=trackSelectOptions, trackInfo=trackInfo)
    trackSelectionView = songSelectionView()
    trackSelectionView.add_item(trackSelectOptionMenu)

    print("here")

    return trackSelectionView

async def createDiscordSelectOptions(label, value, description):
    selectOption = discord.SelectOption(label=label, value=value, description=description)
    
    return selectOption
