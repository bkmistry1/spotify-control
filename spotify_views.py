from typing import List
import discord

from discord.ui import View, Select, Button
from discord.utils import MISSING


class songSelectionView(View):
    def __init__(self):
        super().__init__()


class songSelectList(Select):
    def __init__(self) -> None:
        super().__init__()

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Selected: ")
        return