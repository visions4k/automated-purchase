import discord
import asyncio
import requests
import datetime
from discord import app_commands
from datetime import timedelta
from discord.ext import tasks

# log channel id, change the id in on_ready as well
logs_channel_id = channelID


intents = discord.Intents.default()
intents.members = True # needed
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client) # for slash cmd

# this cookie must be in the group, and have "configure avatar items" permissions
cookie = ""
# to check if purchase id has been used (purchase ids get logged to prevent bypassing)
def check_purchase_id(purchase_id):
    with open("usedbuys.txt", "r") as file:
        used_buys = file.read().splitlines()
        return purchase_id in used_buys
    
# probably want to rework a better method for this
@tasks.loop(minutes=15) 
async def check_expired_roles():
    saved_roles = load_role_info()
    current_time = datetime.datetime.now()
    
    for member_id, role_id, start_time, end_time in saved_roles:
        if current_time > end_time:
            guild = client.get_guild(guildID)
            member = guild.get_member(member_id)
            role = guild.get_role(role_id)
            if member and role:
                await member.remove_roles(role)
                
# time save
def load_role_info():
    roles = []
    with open("savedtimed.txt", "r") as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line:
                member_id, role_id, start_time_str, end_time_str = line.split(",")
                start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S.%f")
                end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S.%f")
                roles.append((int(member_id), int(role_id), start_time, end_time))
    return roles

saved_roles = load_role_info()

# listens for username to be sent via dms
@client.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and message.author != client.user:
        logs_channel = client.get_channel(logs_channel_id)
        log_message = discord.Embed(
            title="Username Recieved",
            description=f"User: `{message.author.name}#{message.author.discriminator}`\nMessage: `{message.content}`",
            color=discord.Color.orange()
        )
        await logs_channel.send(embed=log_message)

        ctx = await tree.get_context(message)  
        await tree.dispatch(ctx)  
        return

    await client.process_commands(message) 
    
# to grab user id via username   
def get_user_id(username):
    url = 'https://users.roblox.com/v1/usernames/users'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        'usernames': [username],
        'excludeBannedUsers': True
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            user_data = data["data"][0]
            if "id" in user_data:
                return str(user_data["id"])
            print(user_data["id"])
    return None


## for every choice, the value should be the asset ID for the clothing item. 
## customers must set inventory to public for this to work
@tree.command(name="purchase", description="Command to upgrade to premium/bonus!", guild=discord.Object(id=guildID)) # guild ID
@app_commands.describe(packages='Packages to choose')
@app_commands.choices(packages=[
    discord.app_commands.Choice(name='1 Week Bonus', value=13456613769),
    discord.app_commands.Choice(name='1 Day Premium', value=13456615376),
    discord.app_commands.Choice(name='1 Week Premium', value=13456616286),
    discord.app_commands.Choice(name='2 Week Premium', value=13456614396),
])

async def purchase_command(interaction, packages: discord.app_commands.Choice[int]):
    channel_id = 1117516685944037487  # channel you want the command ran in
    if interaction.channel_id != channel_id:
        return
    user = interaction.user
 # roles for each package/value. make sure you change the role id and value to corrospond correctly
 # easily can rework to not set a duration, it will be more stable as well since you dont have to check for expired roles
    package_roles = {
        13456613769: {
            'role_id': 1107749003648577566,
            'duration': timedelta(weeks=1)
        },
        13456615376: {
            'role_id': 1107746543693463563,
            'duration': timedelta(days=1)
        },
        13456616286: {
            'role_id': 1107746543693463563,
            'duration': timedelta(weeks=1)
        },
        13456614396: {
            'role_id': 1107746543693463563,
            'duration': timedelta(weeks=2)
        }
    }

    logs_channel = client.get_channel(logs_channel_id)
    log_message = discord.Embed(
        title="Purchase Command",
        description=f"Purchase command used\nUser: `{user.name}#{user.discriminator}`\nOption: `{packages.name}`",
        color=discord.Color.orange()
    )
    await logs_channel.send(embed=log_message)

    ## change with the correct urls. 
    url_1_week_bonus = "https://www.roblox.com/catalog/13456613769/Bonus"
    url_1_day_premium = "https://www.roblox.com/catalog/13456615376/Prem1DAY"
    url_1_week_premium = "https://www.roblox.com/catalog/13456616286/Premium"
    url_2_week_premium = "https://www.roblox.com/catalog/13456614396/Prem2Week"

    embed_channel = discord.Embed(
        title="DM Sent",
        description=f"{user.mention} | Please check your DMs to upgrade. \nIf you did not receive a DM, make sure DMs are on.\nAny problems please make a ticket.",
        color=discord.Color.blue()
    )
    channel_message = await interaction.channel.send(embed=embed_channel)

    async def delete_message(): # for purchase channel message
        await asyncio.sleep(10)  
        await channel_message.delete()  

    asyncio.create_task(delete_message())  

    # make sure you change the values to the corrosponding ones above
    if packages.value == 13456613769:
        url = url_1_week_bonus
    elif packages.value == 13456615376:
        url = url_1_day_premium
    elif packages.value == 13456616286:
        url = url_1_week_premium
    elif packages.value == 13456614396:
        url = url_2_week_premium
    else:
        url = ""


    embed = discord.Embed(
        title="Click to purchase the gamepass!",
        url=url,
        description="**YOUR INVENTORY MUST BE SET PUBLIC**\nOnce purchased - please send your **roblox username**\n\nIf you make a mistake typing the username, run the command again!\nAny other problems contact contact support.\n**+ you have 5 minutes to type in a roblox username\n+ all attempts are logged**",
        color=discord.Color.blue()
    )
    await user.send(embed=embed)

    def check(message):
        return message.author == user and message.channel == user.dm_channel

    try:
        message = await client.wait_for("message", check=check, timeout=300)
        response = message.content.strip()

        embed = discord.Embed(
            title="Username Received!",
            description=f"**Username you typed:** {response}\nPlease wait a moment...",
            color=discord.Color.blurple()
        )
        await user.send(embed=embed)

        roblox_username = response
        await asyncio.sleep(2)

        roblox_id = get_user_id(roblox_username)
        if roblox_id is None:
            embed = discord.Embed(
                title="Username Not Found",
                description=f"**Did not find username:** {roblox_username} \nDouble-check the username, if you still have troubles, please make a ticket!",
                color=discord.Color.red()
            )
            logs_channel = client.get_channel(logs_channel_id)
            log_message = discord.Embed(
                title="Username not found",
                description=f"Username not found\nUser: `{user.name}#{user.discriminator}`\nRBX Username: `{roblox_username}`",
                color=discord.Color.red()
            )
            await logs_channel.send(embed=log_message)
            await user.send(embed=embed)
            return

        embed = discord.Embed(
            title="User Found!",
            description=f"**Username:** {roblox_username}\n**UserID:** {roblox_id}\nPlease wait a moment...",
            color=discord.Color.blurple()
        )
        await user.send(embed=embed)

        asset_id = packages.value 

        url = f"https://inventory.roblox.com/v2/assets/{asset_id}/owners?limit=10&sortOrder=Desc"

        headers = {
            "Cookie": f".ROBLOSECURITY={cookie}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.999 Safari/537.36"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            owners = data["data"]

            if owners:
                first_sale = owners[0]  # only grabs first sale (can change if you get multiple sales at a time)
                owner = first_sale.get("owner")

                if owner and "id" in owner:
                    owner_id = owner["id"]
                    if roblox_id == str(owner_id):
                        purchase_id = str(first_sale.get("id"))
                        if check_purchase_id(purchase_id): # if purchase id has been used before
                            logs_channel = client.get_channel(logs_channel_id)
                            notifymessage = f"<@&1107748390881730751>" # set the role you want to be pinged 
                            await logs_channel.send(notifymessage)
                            logs_channel = client.get_channel(logs_channel_id)
                            log_message = discord.Embed(
                                title="BYPASS DETECTED",
                                description=f"**BYPASS DETECTED**\nDiscord User: `{user.name}#{user.discriminator}`\nUsername: `{roblox_username}`\nUserID: `{roblox_id}`\nPurchaseID: `{purchase_id}`",
                                color=discord.Color.red()
                            )
                            await logs_channel.send(embed=log_message)
                            embed = discord.Embed(
                                title="**Bypass detected**",
                                description=f"The purchase ID `{purchase_id}` has **already been used**. This has been logged and staff team is notified.\nIf mistake, make ticket!",
                                color=discord.Color.red()
                            )
                            await user.send(embed=embed)
                            return
                        else:
                            with open("usedbuys.txt", "a") as file:
                                file.write(purchase_id + "\n")
                        guild = client.get_guild(guildID) # guild ID
                        member = await guild.fetch_member(user.id)
                        print(user.id)
                        
                        
                        logs_channel = client.get_channel(logs_channel_id)
                        notifymessage = f"<@&1107748390881730751>" # set the role you want to be pinged
                        await logs_channel.send(notifymessage)
                        log_message = discord.Embed(
                            title="Successful Sale",
                            description=f"**Successful sale**\nDiscord User: `{user.name}#{user.discriminator}`\nRBX Username: `{roblox_username}`\nUserID: `{roblox_id}`\nPurchaseID: `{purchase_id}`",
                            color=discord.Color.green()
                        )
                        await logs_channel.send(embed=log_message)

                        package = package_roles.get(packages.value)
                        role = guild.get_role(package['role_id'])
                        await member.add_roles(role)
                        save_role_info(member.id, role.id, package['duration'])

                        embed = discord.Embed(
                            title="Sale Found!",
                            description=f"**Username:** {roblox_username}\n**UserID:** {roblox_id}\n**UPGRADE TYPE:** {packages.name}\nYou should have now received the role!",
                            color=discord.Color.green()
                        )
                        await user.send(embed=embed)
                        await asyncio.sleep(package['duration'].total_seconds())
                        await member.remove_roles(role)
                    else:
                        embed = discord.Embed(
                            title="Sale not found",
                            description=f"**Sale not found**\n**UserID:** {roblox_id}\n**Username:**{roblox_username}\nDouble-check the Username & UserID, if you still have troubles, please make a ticket!",
                            color=discord.Color.red()
                        )
                        logs_channel = client.get_channel(logs_channel_id)
                        log_message = discord.Embed(
                            title="Sale Not Found",
                            description=f"Username wrong / inventory private\nUser:`{user.name}#{user.discriminator}`\nRBX Username: `{roblox_username}`\nUserID: `{roblox_id}`",
                            color=discord.Color.red()
                        )
                        await logs_channel.send(embed=log_message)
                        await user.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Error",
                        description="**Inventory is private or username is wrong! Please redo the command.** \nIf you're still having troubles, please make a ticket!",
                        color=discord.Color.red()
                    )
                    logs_channel = client.get_channel(logs_channel_id)
                    log_message = discord.Embed(
                        title="Sale Not Found",
                        description=f"Username wrong / inventory private\nUser:`{user.name}#{user.discriminator}`\nRBX Username: `{roblox_username}`\nUserID: `{roblox_id}`",
                        color=discord.Color.red()
                    )
                    await logs_channel.send(embed=log_message)
                    await user.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="**Failed to fetch sales ; please make a ticket!**",
                    color=discord.Color.red()
                )
                logs_channel = client.get_channel(logs_channel_id)
                log_message = f"Failed to fetch sales @everyone | DM VISIONS: cookie fucced up or sum: {user.name}#{user.discriminator} (Username: {roblox_username}, UserID: {roblox_id})"
                await logs_channel.send(log_message)
                await user.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                description="**Failed to fetch sales ; please make a ticket!**",
                color=discord.Color.red()
            )
            logs_channel = client.get_channel(logs_channel_id)
            log_message = f"@everyone | DM VISIONS: cookie fucced up or sum: {user.name}#{user.discriminator} (Username: {roblox_username}, UserID: {roblox_id})"
            await logs_channel.send(log_message)
            await user.send(embed=embed)
            

    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="Time Expired",
            description="**You took too long to reply! Please run the command again.** \nIf you're still having troubles, please make a ticket!",
            color=discord.Color.red()
        )
        await user.send(embed=embed)
        logs_channel = client.get_channel(logs_channel_id)
        log_message = discord.Embed(
            title="Timeout",
            description=f"User took too long to respond L\nUser: `{user.name}#{user.discriminator}`",
            color=discord.Color.orange()
        )
        await logs_channel.send(embed=log_message)
        
        
def save_role_info(member_id, role_id, duration):
    with open("savedtimed.txt", "a") as file:
        current_time = datetime.datetime.now()
        end_time = current_time + duration
        file.write(f"{member_id},{role_id},{current_time},{end_time}\n")
        

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=guildID)) # guild ID
    print("Ready!")

    logs_channel_id = channelID # log channel ID
    logs_channel = client.get_channel(logs_channel_id)
    log_message = "Bot ready - commands loaded"
    await logs_channel.send(log_message)

    # loads all the saved times
    saved_roles = load_role_info()

    # removes roles within time range
    current_time = datetime.datetime.now()
    for member_id, role_id, start_time, end_time in saved_roles:
        if current_time > end_time:
            guild = client.get_guild(guildID) # guild ID
            member = guild.get_member(member_id)
            role = guild.get_role(role_id)
            if member and role:
                await member.remove_roles(role)

    print("Bots ready - Roles configured")

## discord token
client.run("token here")
