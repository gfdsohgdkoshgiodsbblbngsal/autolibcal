import discord
from discord.ext import commands
from discord import app_commands

import pickle

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(hidden=True)
    @commands.is_owner()
    async def get_caches(self, ctx):
        with open('stored_rooms.dat', 'rb') as file:
            stored_rooms = pickle.load(file)
        
        cache_embed = discord.Embed(title="[DEBUG] Cached Data",
                                    colour=discord.Colour.light_gray())
        cache_embed.add_field(name="Stored Rooms",
                              value=f"```{stored_rooms}```")
        cache_embed.add_field(name="Last Available Day",
                              value=f"```{self.bot.last_response}```")
        
        await ctx.send(embed=cache_embed)

async def setup(bot):
    await bot.add_cog(Debug(bot))