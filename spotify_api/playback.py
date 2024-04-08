import requests
import discord
from discord.ext import commands

from spotifycmds import userTokenById, refreshToken
from data.mongoFunctions import *

async def getQueue(bot: commands.Bot):

    allHosts = await findFromDb(colName="currentHostSessions", dict={})    

    for host in allHosts:
        token = await userTokenById(userId=host["userId"])
        channel: discord.TextChannel = await bot.fetch_channel(host["channelId"])
        message = await channel.fetch_message(host["messageId"])        

        headers = {}

        headers["Authorization"] = "Bearer " + token

        url = "https://api.spotify.com/v1/me/player"

        response = requests.get(url=url, headers=headers)

        if(response.status_code == 401):
            await refreshToken(host["userId"])
            continue
        if(response.status_code == 204):
            continue

        responseJson = response.json()     

        embed = message.embeds[0]

        currentlyPlayingArtists = " by "

        if(responseJson["item"] is not None):
            for artist in responseJson["item"]["artists"]:
                currentlyPlayingArtists += artist["name"] + ", "
                currentlyPlayingArtists = currentlyPlayingArtists[:-2]        

            await embedFieldSet(
                embed=embed, 
                name="Currently Playing", 
                value=responseJson["item"]["name"] + currentlyPlayingArtists,
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

        usersAddedQueueInfo = await findOneFromDb(colName="currentHostSessions", dict={"userId": host["userId"]})
        # userQueue = usersAddedQueueInfo["userQueue"]

        queueString = await listeningQueue(userId=host["userId"], usersAddedQueueInfo=usersAddedQueueInfo)

        # userQueueString = ""
        # for songs in userQueue:
        #     user = await bot.fetch_user(songs["addedBy"])
            # userQueueString += songs["songName"] + " - " + user.name + "\n"
        
        # await embedFieldSet(
        #     embed=embed, 
        #     name="User Queue", 
        #     value=userQueueString,
        #     inline=False,
        # )

        await embedFieldSet(
            embed=embed, 
            name="Queue", 
            value=queueString,
            inline=False,
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


async def listeningQueue(userId, usersAddedQueueInfo):

    token = await userTokenById(userId=userId)
    url = "https://api.spotify.com/v1/me/player/queue"

    headers = {}
    headers["Authorization"] = "Bearer " + token

    response = requests.get(url=url, headers=headers)
    responseJson = response.json()

    queueString = ""
    userQueue = usersAddedQueueInfo["userQueue"]

    for index, track in enumerate(responseJson["queue"]):
        # queueString += str(index+1) + ". " + track["name"] + " by "

        songString = ""
        songString += track["name"] + " by "

        if(track["type"] == "track"):
            for artist in track["artists"]:
                songString += artist["name"] + ", "
        else:
            songString += track["show"]["publisher"] + ", "

        songString = songString[:-2]

        addedBy = ""
        if(len(userQueue) > 0):
            songCheck = next((x for x in userQueue if x["songName"] == songString), None)
            if(songCheck is not None):
                addedBy = " - " + songCheck["addedBy"]
                userQueue.remove(songCheck)

        songString = str(index+1) + ". " + songString + addedBy
        queueString += songString
        queueString += "\n"
            

    for remainingQueueTracks in userQueue:
        await findOneAndUpdate(colName="currentHostSessions", filter={"userId": userId}, dict={"$pull": {"userQueue": {"songName": remainingQueueTracks["songName"]}}})
    return queueString