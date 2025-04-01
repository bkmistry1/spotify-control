import random
import requests

class SongNode():
    def __init__(self, name, uri, artists):
        self.name = name
        self.uri = uri
        self.artists = artists
        self.next = None

async def getSpotifyQueue(userId, token):

    headers = {}
    headers["Authorization"] = "Bearer " + token

    url = "https://api.spotify.com/v1/me/player/queue"

    response = requests.get(url=url, headers=headers)
    if(response.status_code == 401):
        return 401

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