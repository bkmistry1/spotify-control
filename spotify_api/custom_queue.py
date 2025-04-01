import random
import requests
import base64

from env_variables import *

from data.mongoFunctions import *

class SongNode():
    def __init__(self, name, uri, artists):
        self.name = name
        self.uri = uri
        self.artists = artists
        self.next = None

async def refreshToken(userId):
    spotifyTokenDoc = await findOneFromDb(colName="spotifyTokens", dict={"userId": userId})

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
        await deleteOneFromDb(colName="spotifyTokens", dict={"userId": userId})
        await insertIntoCollection(colName="spotifyTokens", mydict={"userId": userId, "token": responseJson})

    return response.status_code

async def getSpotifyQueue(userId, token):

    headers = {}
    headers["Authorization"] = "Bearer " + token

    url = "https://api.spotify.com/v1/me/player/queue"

    response = requests.get(url=url, headers=headers)
    if(response.status_code == 401):
        statusCode = await refreshToken(userId=userId)
        if(statusCode != 200):
            return 401
        else:
            response = requests.get(url=url, headers=headers)

    responseJson = response.json()

    queue = responseJson["queue"]

    return queue

async def shuffleSongs(allSongs):

    shuffledList = SongNode(name=None, uri=None, artists=None)

    tempList = []

    for song in allSongs:
        tmpSongNode = SongNode(name=song["name"], uri=song["uri"], artists = song["artists"])
        tempList.append(tmpSongNode)

    currentNode = shuffledList
    while(len(tempList) > 0):
        index = random.randint(0, len(tempList)-1)
        currentNode.next = tempList[index]
        currentNode = currentNode.next
        tempList.pop(index)

    return shuffledList.next