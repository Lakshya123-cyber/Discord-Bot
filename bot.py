import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl
from random import choice

youtube_dl.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)

        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


client = commands.Bot(command_prefix="?")  # ? is the prefix

status = ["Minecraft", "Sleeping", "Programming", "Chatting"]


@client.event
async def on_ready():
    change_status.start()
    print("Bot is Online")


@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guil.channels, name="general")
    await channel.send(
        f"Welcome {member.mention}! Ready to jam out? see `?help` command for details "
    )


@client.command(name="ping", help="This is a ping command")
async def ping(ctx):
    await ctx.send(f"**Pong!** Latency: {round(client.latency * 1000)}ms")


@client.command(name="hello", help="This is a hello command")
async def hello(ctx):
    responses = [
        "**grumble** Why did you wake me up?",
        "Top of the morning to you lad!",
        "Oh Hullo",
        "Suiiiiiii",
    ]
    await ctx.send(choice(responses))


@client.command(name="die", help="this cammand returns a random last word")
async def die(ctx):
    responses = [
        "why have you brought my short life to an end",
        "I could have done so much more",
        "I have a family, kill them",
    ]
    await ctx.send(choice(responses))


@client.command(name="credits", help="this command returns the credits")
async def credits(ctx):
    await ctx.send("Make by `@d#7976` / `Lakshya Raikwal` / `@titan1728`")


@client.command(name="play", help="This command plays music")
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("You aren't connected to a voice channel")
        return
    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(
            player, after=lambda e: print("Player Error: %s" % e) if e else None
        )

    await ctx.send("**Now Playing:** {}".format(player.title))


@client.command(name="stop", help="This command stops the music")
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()


@tasks.loop(seconds=20)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))


client.run("OTQxMTg5NzQ1MDgwNDA2MDU3.YgSVQQ.nN386WOW46UIOkpj1s3d5XAsKog")