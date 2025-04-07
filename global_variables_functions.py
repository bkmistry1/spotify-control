import discord

spotifyHostViewsDict = {}
userTokensValidDict = {}

async def addViewToDict(channelId, view):
    spotifyHostViewsDict[channelId] = view
    return

async def addUserTokenToDict(userId):
    userTokensValidDict[userId] = True
    return

async def getViewFromDict(channelId):
    return spotifyHostViewsDict[channelId]

async def labelValueCheck(labelValueString: str):
    if(len(labelValueString) > 100):
        subtractString = 99 - len(labelValueString)
        return labelValueString[:subtractString]
    return labelValueString
    
async def createDiscordSelectOptions(label, value, description):
    selectOption = discord.SelectOption(label=label, value=value, description=description)
    return selectOption

class SelectOptionsNode():
    def __init__(self, next, previous, options):
        self.next: SelectOptionsNode = next
        self.previous: SelectOptionsNode = previous
        self.options = options