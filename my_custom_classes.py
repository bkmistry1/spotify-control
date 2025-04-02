

class SongNode():
    def __init__(self, name, uri, artists):
        self.name = name
        self.uri = uri
        self.artists = artists
        self.next = None

    async def getArtistsString(self):
        nextUpArtistString = ""
        for artist in self.artists:
            nextUpArtistString += artist["name"] + ", "

        nextUpArtistString = nextUpArtistString.removesuffix(", ")        

        return nextUpArtistString
    
    async def getSongName(self):
        return self.name