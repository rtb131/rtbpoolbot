import credentials
import discord
import requests
import json
import asyncio
from datetime import datetime
from numerize import numerize


# Set the API key in credentials.py according to the key you see in your blockfrost dashboard.
# You can create a blockfrost API key for free on https://blockfrost.io/
blockfrost_api_key = credentials.blockfrost_api_key

# Set the bot token in credentials.py according to the token you got from the dev web interface (https://discord.com/developers/applications)
# Tutorial on how to create a Discord bot account: https://discordpy.readthedocs.io/en/stable/discord.html
bot_token = credentials.bot_token

# Please change the channel id to the channel you want the bot to send delegator updates in
bot_channel_id = 898682445174546435 

client_id = credentials.client_id
api_base_url = 'https://cardano-mainnet.blockfrost.io/api/v0'
headers = {'Accept': 'application/json', 'project_id': blockfrost_api_key}
pool_id = 'pool1uyttlymyw5t9jfrett3l9hdqr2623yads3z2zdjd6kyxkg8hpn7'
idx = 0


class RtbPoolBotClient(discord.Client):
    async def background_task():
        await client.wait_until_ready()
        
        global current_delegators
        global last_delegator_count

        last_delegator_count = -1
        channel = client.get_channel(id=bot_channel_id)

        while not client.is_closed():

            req = requests.get(f"{api_base_url}/pools/{pool_id}", headers=headers).text
            data = json.loads(req)

            current_delegators = data["live_delegators"]
            live_stake = round(int(data["live_stake"]) / 1000000, 2)
            active_stake = round(int(data["active_stake"]) / 1000000, 2)

            if last_delegator_count != -1:
                if current_delegators > last_delegator_count:

                    # --------------- DISCORD EMBED CODE ---------------
                    embedVar = discord.Embed(title="New Delegator", description="🩸 A new delegator joined [RTB] pool! 🩸\n⠀", color=0xff0000)
                    embedVar.add_field(name="Delegators", value=str(last_delegator_count) + " 🠮 " + str(current_delegators) + "\n⠀", inline=False)
                    embedVar.add_field(name="Total Stake", value="Live: " + str(live_stake) + " ₳\n" + "Active: " + str(active_stake) + " ₳\n⠀", inline=False)
                    embedVar.add_field(name="Join [RTB]", value="[on pool.pm](https://pool.pm/e116bf936475165924795ae3f2dda01ab4a893ad8444a1364dd5886b/stake)", inline=False)
                    embedVar.add_field(name="\u200B", value="Visit https://raisondetrertb.art/stake for more info.")
                    # --------------- DISCORD EMBED CODE ---------------

                    await channel.send(embed=embedVar)

            last_delegator_count = current_delegators

            await RtbPoolBotClient.switch_presence_text(current_delegators, live_stake)
            
            # request status every 20 seconds
            await asyncio.sleep(20)


    async def switch_presence_text(current_delegators, live_stake):
        global idx
        presence_text = [
            "Charles",
            f"{current_delegators} Delegators",
            f"{numerize.numerize(live_stake)} ₳ Live Stake"
        ]

        if "₳" in presence_text[idx]:
            activity_type = discord.ActivityType.watching
        else:
            activity_type = discord.ActivityType.listening

        await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=activity_type, name=presence_text[idx]))
        idx = (idx + 1) % len(presence_text)
        

    async def on_ready(self):
        print('------')
        print('Starting Bot')
        print(f"Name: {self.user.name}")
        print(f"ID: {self.user.id}")
        print('------')
        client.loop.create_task(RtbPoolBotClient.background_task())


    async def on_message(self, message):
        # bot should not reply to itsself
        if message.author.id == self.user.id:
            return

        if message.content.startswith('!pool'):
            try:
                
                # request delegator data
                req = requests.get(f"{api_base_url}/pools/{pool_id}", headers=headers).text

                data = json.loads(req)
                live_delegators = data["live_delegators"]
                live_stake = round(int(data["live_stake"]) / 1000000, 2)
                active_stake = round(int(data["active_stake"]) / 1000000, 2)

                if live_stake < 0.01:
                    live_stake = 0

                if active_stake < 0.01:
                    active_stake = 0

                blocks_minted = data["blocks_minted"]

                # request current epoch data
                req = requests.get(f"{api_base_url}/epochs/latest", headers=headers).text
                
                data = json.loads(req)
                current_epoch = data["epoch"]
                end_time = data["end_time"]
                next_epoch = datetime.utcfromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')


                # --------------- DISCORD EMBED CODE ---------------
                embedVar = discord.Embed(title="[RTB] Stake Pool", description="All of our staking rewards will be used\ntowards project development and our community.\n\nTicker: [RTB]\nPledge: 3k ₳\nMargin: 1%\nFixed: 340 ₳\n⠀", color=0xff0000)
                embedVar.add_field(name="Total Stake", value="Live: " + str(live_stake) + " ₳\n" + "Active: " + str(active_stake) + " ₳\n⠀", inline=True)
                embedVar.add_field(name="Delegators", value=str(live_delegators) + "\n⠀", inline=True)
                embedVar.add_field(name="Epoch " + str(current_epoch), value="Blocks Minted: " + str(blocks_minted) + "\n" + "Next Epoch: " + str(next_epoch) + " (UTC)\n⠀", inline=False)
                embedVar.add_field(name="Join [RTB]", value="[on pool.pm](https://pool.pm/e116bf936475165924795ae3f2dda01ab4a893ad8444a1364dd5886b/stake)", inline=False)
                embedVar.add_field(name="\u200B", value="Visit https://raisondetrertb.art/stake for more info.")
                # --------------- DISCORD EMBED CODE ---------------

                await message.channel.send(embed=embedVar)

            except:
                await message.reply("Could not fetch data from blockfrost API", mention_author=True)


client = RtbPoolBotClient()
client.run(bot_token)
