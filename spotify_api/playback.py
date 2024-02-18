import requests

from spotifycmds import userTokenById

async def getQueue(userId):

    token = await userTokenById(userId=userId)

    headers = {}

    headers["Authorization"] = "Bearer " + token

    url = "https://api.spotify.com/v1/me/player"

    response = requests.get(url=url, headers=headers)

    responseJson = response.json()

    
    return 