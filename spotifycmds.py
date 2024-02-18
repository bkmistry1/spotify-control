import requests
import random
import string
import base64

from env_variables import *
from views import *
from data.mongoFunctions import *
from spotify_views import *
from view_functions import *


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

async def refreshToken(interaction: discord.Interaction):
    spotifyTokenDoc = await findOneFromDb(colName="spotifyTokens", dict={"userId": interaction.user.id})

    stringToEncode: str = clientId + ":" + clientSecret
    encodedClientIdSecret = base64.b64encode(stringToEncode.encode("ascii"))

    token = spotifyTokenDoc["token"]["access_token"]
    refresh_token = spotifyTokenDoc["token"]["refresh_token"]

    params = {}
    params["grant_type"] = "refresh_token"
    params["refresh_token"] = refresh_token

    headers = {}
    headers["content-type"] = "application/x-www-form-urlencoded"
    headers["Authorization"] = "Basic " + encodedClientIdSecret.decode("ascii")

    url = "https://accounts.spotify.com/api/token"

    response = requests.post(url=url, headers=headers, params=params)
    responseJson = response.json()
    responseJson["refresh_token"] = refresh_token

    if(response.status_code == 200):
        await deleteOneFromDb(colName="spotifyTokens", dict={"userId": interaction.user.id})
        await insertIntoCollection(colName="spotifyTokens", mydict={"userId": interaction.user.id, "token": responseJson})
        # await findOneAndUpdate(colName="spotifyTokens", filter={"userId": interaction.user.id}, dict={"$update": {"token": {"access_token": responseJson["access_token"]}}})

    return response.status_code

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
    scope = "user-read-private%20user-read-email%20user-read-playback-state%20user-modify-playback-state%20user-read-currently-playing"

    userCheck = await findOneFromDb(colName="spotifyUsers", dict={"userId": interaction.user.id})
    if(userCheck is None):
        await insertIntoCollection(colName="spotifyUsers", mydict={"userId": interaction.user.id, "userName": interaction.user.name, "state": state})
    else:
        await findOneAndUpdate(colName="spotifyUsers", filter={"userId": interaction.user.id}, dict={"$set": {"state": state}})

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

    tokenCheck = await findOneFromDb(colName="spotifyTokens", dict={"userId": interaction.user.id})
    if(tokenCheck is None):
        await insertIntoCollection(colName="spotifyTokens", mydict={"userId": interaction.user.id, "token": responseJson})
    else:
        await findOneAndUpdate(colName="spotifyTokens", filter={"userId": interaction.user.id}, dict={"$set": {"token": responseJson}})

    return

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
                refreshCheck = await refreshToken(interaction=interaction)
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

    trackInfo = {}
    trackSelectOptions = []

    for song in listOfSongs:
        if(song["name"] + " by " + song["artists"][0]["name"] in trackInfo.keys()):
            continue
        trackInfo[song["name"] + " by " + song["artists"][0]["name"]] = song["uri"]
        trackSelectOption = await createDiscordSelectOptions(label=str(song["name"] + " by " + song["artists"][0]["name"]), value=str(song["name"] + " by " + song["artists"][0]["name"]), description=str(song["artists"][0]["name"]))
        trackSelectOptions.append(trackSelectOption)
        # await addSongToQueue(interaction=interaction, songUri=song["uri"])

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

async def createDiscordSelectOptions(label, value, description):
    selectOption = discord.SelectOption(label=label, value=value, description=description)
    return selectOption

async def spotifyHost(interaction: discord.Interaction):
    
    guild = interaction.guild

    # create new category
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    
    newCategory = await guild.create_category(name=interaction.user.name + " Spotify Host", overwrites=overwrites)
    await newCategory.set_permissions(target=interaction.user, read_messages=True, send_messages=True)

    # create new text channel
    channel = await newCategory.create_text_channel('host', overwrites=overwrites)
    await channel.set_permissions(target=interaction.user, read_messages=True, send_messages=True)
    
    hostView = spotifyHostView()
    hostView.hostId = interaction.user.id

    hostEmbed = discord.Embed(
        title="Spotify Host: " + interaction.user.name,
        description="Add Songs to the Host's Queue",
        color=discord.Color.blue()
    )

    hostEmbed.add_field(name="", value="", inline=False)
    hostEmbed.add_field(name="Currently Playing", value="None", inline=False)
    hostEmbed.add_field(name="Progress", value="None", inline=True)
    hostEmbed.add_field(name="Length", value="None", inline=True)
    hostEmbed.add_field(name="Queue", value="None", inline=False)

    hostSessionMsg = await channel.send(embed=hostEmbed, view=hostView)

    await insertIntoCollection(
        colName="currentHostSessions", 
        mydict = {
            "userId": interaction.user.id, 
            "messageId": hostSessionMsg.id,
            "channelId": hostSessionMsg.channel.id,
        }
    )
    # await interaction.followup.send(embed=hostEmbed, view=hostView)
    await interaction.followup.send("Done", ephemeral=True)

    return


# create play function

# create pause function

# create next function

# create previous function

# create volume up function

# create volume down function

# create display queue function
