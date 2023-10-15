#libraries
from re import A, M
#from this import d
from typing import Union
from xml.dom.xmlbuilder import DOMEntityResolver
import discord
from discord import option
import os #default module
from dotenv import load_dotenv
import sqlite3
import random
import asyncio
import time

# Loads the token file 
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

VISITORS_NUMBER = 3
# Constantes and global variables
cooldown = None
count = 0
# The footer text
FOOTER_TEXT = "In moon we goon"

## MUST REWORK (Temporary Solution)
visitorTimeout = False # basically one needs to be true and one needs to be false in order to activate the timeout thingy 
visitorTimeout2 = True

MAX_VISITOR_TIMEOUT = 60 # 300
MIN_VISIT_TIME = 10 #This is the variable to change the minimum random time for a visitor to appear 600
MAX_VISIT_TIME = 20 #THis is the variable to change the maximum random time for a visitor to appear 900

# the discord server that will have access to the commands (change this later)
bot = discord.Bot(debug_guilds=[982666098551955518])

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

# Command for the user to configure the bot
@bot.slash_command(name="configure", description="Use this command to configure the entrance door",)
@option("enable", description="Whether to enable the bot or not")
@option(
    "channel",
    discord.TextChannel,
    # You can specify allowed channel types by passing a union of them like this.
    description="Pick a channel to be used as the entrance door, where trick-or-treaters will arrive",
    required=False,
)
async def select_channel(
    ctx: discord.ApplicationContext,
    enable: bool,
    channel: discord.TextChannel,
): 
    # connects to the database
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute(f"SELECT channel_id FROM channel WHERE guild_id = {ctx.guild.id}")
    result = cursor.fetchone()
    if result is None:
        sql = ("INSERT INTO channel(guild_id, channel_id) VALUES(?,?)")
        val = (ctx.guild.id, channel.id)
        await ctx.respond(f"{channel.mention} has been configured as the entrance door.")
    elif result is not None:
        sql = ("UPDATE channel SET channel_id = ? WHERE guild_id = ?")
        val = (channel.id, ctx.guild.id)
        await ctx.respond(f"Entrance door has been updated to {channel.mention}")
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()

@bot.command(description="Sends the bot's latency.") # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")


# Command to fetch the server leaderboard
@bot.command(description="Get server leaderboard")
async def leaderboard(ctx):
    guild_name = bot.get_guild(ctx.guild.id)
    boardEmbed=discord.Embed(title=f"Top treaters in {guild_name}")

    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()
    cursor.execute(f"SELECT user_id, score FROM main WHERE guild_id = {ctx.guild.id} ORDER BY score DESC")
    index = 1
    for i in cursor:
        member = i[0]
        score = i[1]
        boardEmbed.add_field(name="------", value =f"**{index}.** <@{member}> - {score} ", inline = False)
        index += 1
    cursor.close()
    db.close()
    await ctx.respond(embed=boardEmbed)
    
class MyDisabled(discord.ui.View):
    @discord.ui.button(label="Give a treat", row=0, style=discord.ButtonStyle.primary, emoji="🍬", disabled=True)
    async def first_button_callback(self, button, interaction):
        print("clicked first button")
    @discord.ui.button(label="Show a trick", row=0, style=discord.ButtonStyle.primary, emoji="👻", disabled=True)
    async def second_button_callback(self, button, interaction):
        print("clicked second button")

class MyOptions(discord.ui.View):
    global on_timeout     
    async def on_timeout(self):
        timeoutEmbed=discord.Embed(title=f"Uh oh! 💀", description=f"It seems that nobody has answered the door, \n so {name} took it personally and wrote a rant on Twitter.com", color=0xff8000)
        timeoutEmbed.set_footer(text=FOOTER_TEXT)
        timeoutEmbed.set_image(url="https://media.giphy.com/media/XIqCQx02E1U9W/giphy.gif")
        for child in self.children:
            child.disabled = True
        await self.message.edit(embed=timeoutEmbed, view=self)

    @discord.ui.button(label="Give a treat", row=0, style=discord.ButtonStyle.primary, emoji="🍬")
    async def first_button_callback(self, button, interaction):
        for child in self.children:
            child.disabled = True
        treatEmbed=discord.Embed(title=f"Happy Halloween!", description=f"As a thank you for your kindness,\n they give <@{interaction.user.id}> {reward}", color=0xff8000)
        treatEmbed.set_footer(text=FOOTER_TEXT)
        treatEmbed.add_field(name="Item Description", value=f"*{rewardDescription}*", inline=False)
        treatEmbed.set_image(url=visURL)
        treatEmbed.set_thumbnail(url=rewardPicture)
        await interaction.response.edit_message(embed=treatEmbed, view=self)
        db = sqlite3.connect("main.sqlite")
        cursor = db.cursor()

        cursor.execute(f"SELECT score FROM main WHERE user_id = {interaction.user.id} AND guild_id = {interaction.guild.id}")
        result = cursor.fetchone()
        if result is None:
            sql = ("INSERT INTO main(guild_id, user_id, score) VALUES (?,?,?)")
            val = (interaction.guild.id, interaction.user.id, 1)
        elif result is not None: 
            sql = ("UPDATE main SET score = ? WHERE user_id = ? AND guild_id = ?")
            val = (result[0] + 1, interaction.user.id, interaction.guild.id)
        cursor.execute(sql, val)
        db.commit()
        cursor.execute(f"SELECT visitor_visits FROM visitors WHERE visitor_id = {currentVisitorID}")
        visits = cursor.fetchone()
        if visits is None:
            sql = ("INSERT INTO visitors(visitor_id, visitor_visits) VALUES (?,?)")
            val = (currentVisitorID, 1)
        elif visits is not None:
            sql = ("UPDATE visitors SET visitor_visits = ? WHERE visitor_id = ?")
            val = (visits[0] + 1, currentVisitorID)
        cursor.execute(sql, val)
        db.commit()

        #Creates a table for keeping track of user points over time 
        ts = time.time()
        #print(ts)
        cursor.execute(f"CREATE TABLE IF NOT EXISTS '{interaction.guild.id}'(unix REAL)")
        cursor.execute(f"INSERT INTO '{interaction.guild.id}'(unix) VALUES (?)", (ts,))
        db.commit()
        # Toggle the timeout to false
        global visitorTimeout
        global visitorTimeout2
        visitorTimeout = False
        visitorTimeout2 = False
        cursor.execute(f"SELECT user_id, winner_status, ranking, score FROM main WHERE guild_id = {interaction.guild.id} ORDER BY score DESC")
        result = cursor.fetchall()
        #print(result)
        index = 1
        for i in result:
            member_id = i[0]
            member_points = i[3]
            
            # Sets the rank of the user based on the index
            sql = ("UPDATE main SET ranking = ? WHERE user_id = ? AND guild_id = ?")
            val = (index, member_id, interaction.guild.id)
            cursor.execute(sql, val)
            db.commit()

            index += 1
        
        # Refetches so that it can see if a user has passed another user
        cursor.execute(f"SELECT user_id, winner_status, ranking, score FROM main WHERE guild_id = {interaction.guild.id} ORDER BY score DESC")
        result = cursor.fetchall()
        for i in result:
            member_id = i[0]
            member = await interaction.guild.fetch_member(member_id) # fetches member from member ID
            role = discord.utils.get(interaction.guild.roles, name = "Halloween Champion 2023")
            print(i[2])
            if i[2] == 1:
                await member.add_roles(role)
            elif i[2] != 1:
                await member.remove_roles(role)

            # Checks if user column exists, if not then create one
            cursor.execute(f"PRAGMA table_info('{interaction.guild.id}')")
            column = cursor.fetchall()
            users = [fields[1] for fields in column]
            print(users)
            if f'{member_id}' not in users:
                cursor.execute(f"ALTER TABLE '{interaction.guild.id}' ADD COLUMN '{member_id}' TEXT")
            sql = (f"UPDATE '{interaction.guild.id}' SET '{member_id}' = ? WHERE unix = ?")
            val = (member_points, ts)
            cursor.execute(sql, val)
            db.commit()
            #print(i)

        cursor.close()
        db.close()

    # Trick button
    @discord.ui.button(label="Show a trick", row=0, style=discord.ButtonStyle.primary, emoji="👻")
    async def second_button_callback(self, button, interaction):
        trickEmbed=discord.Embed(title=f"Uh oh!", description=f"It seems that your trick went too well, \n {name} was too scared and ran away!", color=0xff8000)
        trickEmbed.set_footer(text=FOOTER_TEXT)
        trickEmbed.set_image(url="https://thumbs.gfycat.com/BarrenNarrowEmu-size_restricted.gif")

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=trickEmbed, view=self)
        global visitorTimeout
        global visitorTimeout2
        visitorTimeout = False
        visitorTimeout2 = False


@bot.event
async def on_message(message):
    global cooldown
    global count

    if count > 1:
        count = 0 
    while message.author.id != bot.user.id and cooldown != True and count < 2: #and count < 2: #Makes sure that the bot doesn't react to their own messages

        while count < 2:

            #Puts the cooldown on
            cooldown = True
            #print(cooldown)
            time = random.randint(MIN_VISIT_TIME, MAX_VISIT_TIME)
            await asyncio.sleep(time)
            count += 1

            db = sqlite3.connect('main.sqlite')
            cursor = db.cursor()
            cursor.execute(f"SELECT channel_id FROM channel WHERE guild_id = {message.guild.id}")
            door = cursor.fetchone()
            channelID = door[0]
            cursor.close()
            db.close()
            global currentVisitorID
            currentVisitorID = random.randint(1, VISITORS_NUMBER)
            #print(currentVisitorID)
            db = sqlite3.connect('main.sqlite')
            cursor = db.cursor()
            cursor.execute(f"SELECT visitor_name, visitor_reward, visitor_pic, reward_description, reward_picture FROM visitors WHERE visitor_id = {currentVisitorID}")
            
            currentVisitor = cursor.fetchone()
            global name
            name = currentVisitor[0]
            global reward
            reward = currentVisitor[1]
            global visURL
            visURL = currentVisitor[2]
            global rewardDescription
            rewardDescription = currentVisitor[3]
            global rewardPicture
            rewardPicture = currentVisitor[4]


            embed=discord.Embed(title=f"A trick-or-treater has appeared! Its {name}!", description="Open the door and click on either options below:", color=0xff8000)
            embed.set_footer(text=FOOTER_TEXT)
            embed.set_image(url=visURL)

            channel = bot.get_channel(channelID)

            msg = await channel.send(embed=embed, view=MyOptions(timeout=None))

            global visitorTimeout
            global visitorTimeout2

            timeoutcounter = 0
            if visitorTimeout2 == True and visitorTimeout == False: #if the default configs are met then activate timeout sequence
                visitorTimeout = True
                visitorTimeout2 = True

            while visitorTimeout == True and visitorTimeout2 == True:
                
                #print(visitorTimeout)
                if visitorTimeout == False and visitorTimeout2 == False:
                    break
                timeoutcounter += 1
                await asyncio.sleep(1)
                if timeoutcounter == MAX_VISITOR_TIMEOUT:
                    timeoutEmbed=discord.Embed(title=f"Uh oh! 💀", description=f"It seems that nobody has answered the door, \n so {name} took it personally and wrote a rant on Twitter.com", color=0xff8000)
                    timeoutEmbed.set_footer(text=FOOTER_TEXT)
                    timeoutEmbed.set_image(url="https://media.giphy.com/media/XIqCQx02E1U9W/giphy.gif")
                    await msg.edit(embed=timeoutEmbed, view=MyDisabled())
                    visitorTimeout = False
                    visitorTimeout2 = True
                    count += 1        

            cursor.close()
            db.close()
            # Resets the visitorTimeout once the timeout is done. 
            if visitorTimeout == False and visitorTimeout2 == False:
                visitorTimeout = False
                visitorTimeout2 = True
            #print(count)
            cooldown = False
    
bot.run(TOKEN)