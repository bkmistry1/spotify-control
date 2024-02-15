import discord
import requests

from data.mongoFunctions import *

async def addSongToQueue(interaction: discord.Interaction, songUri):

    token = await userToken(interaction=interaction)

    params = {}
    params["uri"] = songUri

    headers = {}
    headers["Authorization"] = "Bearer " + token
    
    url = "https://api.spotify.com/v1/me/player/queue"

    response = requests.post(url=url, params=params, headers=headers)
    
    return        


async def userToken(interaction: discord.Interaction):
    tokenInfo = await findOneFromDb(colName="spotifyTokens", dict={"userId": interaction.user.id})
    token = tokenInfo["token"]["access_token"]
    return token  