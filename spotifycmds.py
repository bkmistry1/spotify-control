import requests
import random
import string

from env_variables import *
from views import *
from data.mongoFunctions import *


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

async def getPlaybackDevices(token):
    url = "https://api.spotify.com/v1/me/player/devices"
    headers = {"Authorization": "Bearer " + token}
    params = {}

    response = requests.get(url=url, headers=headers, params=params)
    responseJson = response.json()

    print(responseJson)
    return

async def spotifyGetAuth(interaction: discord.Interaction):
    redirect_uri = 'http://localhost:27695'

    n = 16

    state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))
    scope = "user-read-private%20user-read-email"

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
