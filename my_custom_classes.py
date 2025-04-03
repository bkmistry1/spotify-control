

class SongNode():
    def __init__(self, name, uri, artists):
        self.name = name
        self.uri = uri
        self.artists = artists
        self.next: SongNode = None
        self.queuedBy = None

    async def getArtistsString(self):
        nextUpArtistString = ""
        for artist in self.artists:
            nextUpArtistString += artist["name"] + ", "

        nextUpArtistString = nextUpArtistString.removesuffix(", ")        

        return nextUpArtistString
    
    async def getSongName(self):
        return self.name
    
    async def getLength(self):
        length = 1
        currentNode = self
        while(currentNode.next is not None):
            currentNode = currentNode.next
            length += 1

        return length
            