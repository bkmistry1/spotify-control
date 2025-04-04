import discord

spotifyHostViewsDict = {}

async def addViewToDict(channelId, view):
    spotifyHostViewsDict[channelId] = view
    return

async def getViewFromDict(channelId):
    return spotifyHostViewsDict[channelId]


class SelectOptionsNode():
    def __init__(self, next, previous, options):
        self.next: SelectOptionsNode = next
        self.previous: SelectOptionsNode = previous
        self.options = options