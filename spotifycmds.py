import requests

from env_variables import *

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