from typing import List
import discord

from discord.ui import View, Select, Button
from discord.utils import MISSING


class songSelectionView(View):
    def __init__(self):
        super().__init__()


class songSelectList(Select):
    def __init__(self, options, trackInfo) -> None:
        super().__init__(options=options, min_values=1, max_values=1)
        self.trackInfo = trackInfo

    async def callback(self, interaction: discord.Interaction):
        print(self.values[0])
        print(self.trackInfo[self.values[0]])
        await interaction.response.edit_message(content="Selected: " + self.values[0])
        return