import requests
import discord

from spotifycmds import userTokenById, refreshToken
from data.mongoFunctions import *
from views import PersistentViewBot

async def getQueue(bot: PersistentViewBot):

    allHosts = await findFromDb(colName="currentHostSessions", dict={})    

    for host in allHosts:
        token = await userTokenById(userId=host["userId"])
        channel: discord.TextChannel = bot.get_channel(host["channelId"])
        message = await channel.fetch_message(host["messageId"])        

        headers = {}

        headers["Authorization"] = "Bearer " + token

        url = "https://api.spotify.com/v1/me/player"

        response = requests.get(url=url, headers=headers)

        responseJson = response.json()     

        embed = message.embeds[0]

        await embedFieldSet(
            embed=embed, 
            name="Currently Playing", 
            value=responseJson["item"]["name"],
            inline=False,
        )

        await embedFieldSet(
            embed=embed, 
            name="Progress", 
            value=await convertTime(responseJson["progress_ms"]),
            inline=True,
        )

        await embedFieldSet(
            embed=embed, 
            name="Length", 
            value=await convertTime(responseJson["item"]["duration_ms"]),
            inline=True,
        )                
        

        await message.edit(embed=embed)


    return 

async def embedFieldSet(embed: discord.Embed, name, value, inline):
    for index, field in enumerate(embed.fields):
        if(field.name == name):
            embed.set_field_at(index=index, name=name, value=value, inline=inline)
    return embed

async def convertTime(time):
    millis=time
    millis = int(millis)
    seconds=(millis/1000)%60
    seconds = int(seconds)
    minutes=(millis/(1000*60))%60
    minutes = int(minutes)
    # hours=(millis/(1000*60*60))%24

    # print ("%d:%d" % (minutes, seconds)) 

    if(seconds < 10):
        seconds = "0" + str(seconds)

    return str(minutes) + ":" + str(seconds)