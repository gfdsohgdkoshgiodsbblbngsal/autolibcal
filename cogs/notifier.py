import discord
from discord import app_commands
from discord.ext import commands, tasks

from typing import Optional

from utils import *

import datetime

import re

try:
    import cPickle as pickle
except:
    import pickle

ROOM_NAMES = ["Room B", "Room C", "Room D", "Room E"]
PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")

def find_differences(list1, list2):
    differences = []

    # Iterate over the first dimension
    for i in range(len(list1)):
        sublist1 = list1[i]
        sublist2 = list2[i]

        # Iterate over the second dimension
        for j in range(len(sublist1)):
            innerlist1 = sublist1[j]
            innerlist2 = sublist2[j]

            # Get the maximum length to handle unequal inner lists
            max_length = max(len(innerlist1), len(innerlist2))

            # Iterate over the third dimension
            for k in range(max_length):
                val1 = innerlist1[k] if k < len(innerlist1) else None
                val2 = innerlist2[k] if k < len(innerlist2) else None

                # Compare the elements
                if val1 != val2:
                    differences.append((i, j, k))
    return differences

async def last_available_day(silent=True):
    current_date = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=-7)))
    caught_off = False
    streak = 0
    while True:
        if caught_off and streak >= 7:
            break
        if current_date.weekday() == 5 or current_date.weekday() == 6:
            current_date += datetime.timedelta(days=1)
            continue
        
        response = await get_study_rooms(current_date.strftime("%Y-%m-%d"))
        if isinstance(response, str):
            if not caught_off and not silent:
                print("Missing day detected.")
            caught_off = True
            streak += 1
            if not silent:
                print("Streak:", streak)
        else:
            if caught_off and not silent:
                print("Streak broken.")
            caught_off = False
            streak = 0
            if not silent:
                print(current_date.strftime("%m/%d/%Y"))
        current_date += datetime.timedelta(days=1)
    
    return current_date - datetime.timedelta(days=streak+2)

async def update_stored_rooms():
    current_date = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=-7)))
    date = await last_available_day()
    date -= datetime.timedelta(days=1)

    stored_rooms = []

    while current_date < date:
        response = await get_study_rooms(current_date.strftime("%Y-%m-%d"))
        if isinstance(response, str):
            current_date += datetime.timedelta(days=1)
            continue
        
        rooms, period_names = response[0], response[1]
        period_names = [' '.join(p.split()) for p in period_names]
        
        if len(period_names) != 6:
            current_date += datetime.timedelta(days=1)
            continue
        
        available_rooms = []
        for period in rooms:
            available_rooms.append(list(period[0]))
        
        stored_rooms.append(available_rooms)
        current_date += datetime.timedelta(days=1)

    with open("stored_rooms.dat", "wb") as file:
        pickle.dump(stored_rooms, file)

    return stored_rooms

class Notifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.debug_output = False
        self.detect_new_rooms.start()
        self.detect_new_bookings.start()
        self.bot.detect_room_task = self.detect_new_rooms

    get_group = app_commands.Group(name="get", description="Commands related to getting information")
    
    @get_group.command(name="all", description="Get every room for a specific date. Date format: YYYY-MM-DD")
    async def get_all_rooms(self, interaction: discord.Interaction, date: Optional[str]):
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        date_obj = datetime.datetime.strptime(date+"-0700", "%Y-%m-%d%z")
        
        if not PATTERN.fullmatch(date):
            await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
            return
        
        response = await get_study_rooms(date)
        if isinstance(response, str):
            await interaction.response.send_message(response, ephemeral=True)
            return

        rooms, period_names = response[0], response[1]
        period_names = [' '.join(p.split()) for p in period_names]
        print(period_names)
        
        if len(period_names) != 6:
            await interaction.response.send_message("Error: The day you have requested has an abnormal schedule. Please manually check the website [here](https://mitty.libcal.com/r/new/availability?lid=20936&zone=0&gid=44085&capacity=1).", ephemeral=True)
            return
        
        
        
        embed = discord.Embed(title=f"Available Rooms For <t:{int(date_obj.timestamp())}:d>", # timestamp
                              color=discord.Colour.green())
        for i, period in enumerate(rooms):
            available_rooms = list(period[0])
            period_start = datetime.datetime.strptime(period[1]+"-0700", "%Y-%m-%d %H:%M:%S%z")
            period_end = datetime.datetime.strptime(period[2]+"-0700", "%Y-%m-%d %H:%M:%S%z")

            if len(available_rooms) == 0:
                description = "No rooms available."
            elif len(available_rooms) == 1:
                description = ROOM_NAMES[available_rooms[0]]
            else:
                description = ', '.join([ROOM_NAMES[i] for i in available_rooms[:-1]]) + ', and ' + ROOM_NAMES[available_rooms[-1]]
            
            embed.add_field(name=period_names[i], value=description, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @tasks.loop(seconds=15)
    async def detect_new_rooms(self):
        print("test")
        date = await last_available_day()
        date -= datetime.timedelta(days=1)
        print("Last available day:", date.strftime("%m/%d/%Y"))

        guild = self.bot.get_guild(964386237974728705)
        channel = guild.get_channel(1280989871636221993)
        
        if not hasattr(self.bot, "last_response"):
            self.bot.last_response = date.strftime("%Y-%m-%d")
            warning_embed = discord.Embed(title="Warning",
                                          description="Something went wrong, or the bot has been restarted.",
                                          color=discord.Colour.yellow())
            await channel.send(embed=warning_embed)
            return
        else:
            if date.strftime("%Y-%m-%d") != self.bot.last_response:
                self.bot.last_response = date.strftime("%Y-%m-%d")
            else:
                if self.bot.debug_output:
                    neutral_embed = discord.Embed(title="[DEBUG] No New Rooms Detected",
                                                    description="No new rooms have been detected.",
                                                    color=discord.Colour.light_gray())
                    await channel.send(embed=neutral_embed)
                return

        response = await get_study_rooms(date.strftime("%Y-%m-%d"))
        rooms, period_names = response[0], response[1]
        period_names = [' '.join(p.split()) for p in period_names]
        
        if len(period_names) != 6:
            await channel.send(f"@everyone Error: The day you have requested has an abnormal schedule. Please manually check the website [here](https://mitty.libcal.com/r/new/availability?lid=20936&zone=0&gid=44085&capacity=1).")
            return
        
        print("New rooms detected!")
        await update_stored_rooms()
        
        embed = discord.Embed(title=f"New Rooms Released! <t:{int(date.timestamp())}:d>", # timestamp
                              description="Check the website [here](https://mitty.libcal.com/r/new/availability?lid=20936&zone=0&gid=44085&capacity=1) for more information.",
                              color=discord.Colour.green())
        for i, period in enumerate(rooms):
            available_rooms = list(period[0])
            period_start = datetime.datetime.strptime(period[1]+"-0700", "%Y-%m-%d %H:%M:%S%z")
            period_end = datetime.datetime.strptime(period[2]+"-0700", "%Y-%m-%d %H:%M:%S%z")

            if len(available_rooms) == 0:
                description = "No rooms available."
            elif len(available_rooms) == 1:
                description = ROOM_NAMES[available_rooms[0]]
            else:
                description = ', '.join([ROOM_NAMES[i] for i in available_rooms[:-1]]) + ', and ' + ROOM_NAMES[available_rooms[-1]]
            
            embed.add_field(name=period_names[i], value=description, inline=False)
        
        await channel.send("@everyone", embed=embed)
    
    @tasks.loop(seconds=15)
    async def detect_new_bookings(self): # detect when a room has been booked
        # maybe get the entire available date range?
        # store all those days in a list of lists
        # check if the list of lists has changed
        # use pickle to store this data
        
        # if it has, then send a message
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(964386237974728705)
        channel = guild.get_channel(1280989871636221993)
        
        try:
            with open("stored_rooms.dat", "rb") as file:
                stored_rooms = pickle.load(file)
        except FileNotFoundError:
            stored_rooms = await update_stored_rooms()
        
        if stored_rooms is None:
            await update_stored_rooms()
        
        if self.bot.debug_output:
            await channel.send(f"Stored Rooms: {stored_rooms}")
    
        # check if the stored rooms have changed
        current_date = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=-7)))
        date = await last_available_day()
        date -= datetime.timedelta(days=1)
        
        days = []
        
        new_stored_rooms = []
        while current_date < date:
            response = await get_study_rooms(current_date.strftime("%Y-%m-%d"))
            if isinstance(response, str):
                current_date += datetime.timedelta(days=1)
                continue
            
            rooms, period_names = response[0], response[1]
            period_names = [' '.join(p.split()) for p in period_names]
            
            if len(period_names) != 6:
                current_date += datetime.timedelta(days=1)
                continue
            
            available_rooms = []
            for period in rooms:
                available_rooms.append(list(period[0]))
            
            new_stored_rooms.append(available_rooms)
            days.append(current_date.timestamp())
            
            current_date += datetime.timedelta(days=1)

        print(new_stored_rooms)

        if new_stored_rooms != stored_rooms:
            # Send notification about new booking
            embed = discord.Embed(
                title="New Booking Detected!",
                description=(
                    "A new booking has been detected. Check the website "
                    "[here](https://mitty.libcal.com/r/new/availability?lid=20936&zone=0&gid=44085&capacity=1) "
                    "for more information."
                ),
                color=discord.Colour.green()
            )
            
            differences = find_differences(stored_rooms, new_stored_rooms)
            await channel.send(f"Booking made on <t:{int(days[differences[0][0]])}:d> for {period_names[differences[0][1]]} in {ROOM_NAMES[differences[0][2]]}.")
            
            await channel.send("@here", embed=embed)

            # Update the stored_rooms.dat file
            with open("stored_rooms.dat", "wb") as file:
                pickle.dump(new_stored_rooms, file)
        else:
            if self.bot.debug_output:
                # Send debug message indicating no new bookings 
                neutral_embed = discord.Embed(
                    title="[DEBUG] No New Bookings Detected",
                    description="No new bookings have been detected.",
                    color=discord.Colour.light_gray()
                )
                await channel.send(embed=neutral_embed)
                await channel.send(f"Old: {stored_rooms}\nNew: {new_stored_rooms}")

    @detect_new_rooms.error
    async def detect_new_rooms_error(self, error):
        print(error)

async def setup(bot):
    await bot.add_cog(Notifier(bot))