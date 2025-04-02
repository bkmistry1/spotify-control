class SongNode():
    def __init__(self, name, uri, artists):
        self.name = name
        self.uri = uri
        self.artists = artists
        self.next = None