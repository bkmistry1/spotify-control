
spotifyHostViewsDict = {}

async def addViewToDict(channelId, view):
    spotifyHostViewsDict[channelId] = view
    return

async def getViewFromDict(channelId):
    return spotifyHostViewsDict[channelId]