import discord
from discord.ext import commands
import asyncio
import yt_dlp
import json
import os

# Cargar configuración
with open('config.json', 'r') as f:
    config = json.load(f)

# Configuración de yt-dlp optimizada para fluidez y calidad
ytdl_format_options = {
    'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'age_limit': None,
    'cachedir': False,
    'http_chunk_size': 10485760,  # 10MB chunks para mejor buffering
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'best',
        'preferredquality': '256',
    }],
}

# Opciones optimizadas de FFmpeg para máxima fluidez
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -thread_queue_size 2048',
    'options': '-vn -b:a 256k -ar 48000 -ac 2 -bufsize 2048k -maxrate 256k -filter:a "volume=1.0,equalizer=f=100:width_type=o:width=2:g=2" -fflags +genpts+discardcorrupt'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.8):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.thumbnail = data.get('thumbnail')
        self.duration = self.format_duration(data.get('duration', 0))
        self.webpage_url = data.get('webpage_url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @staticmethod
    def format_duration(seconds):
        if not seconds:
            return "Desconocido"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

class MusicQueue:
    def __init__(self):
        self.songs = []
        self.current = None
        self.voice_client = None
        self.text_channel = None
        self.is_playing = False

    def add_song(self, song):
        self.songs.append(song)

    def get_next(self):
        if self.songs:
            return self.songs.pop(0)
        return None

# Intents y bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=config['prefix'], intents=intents, help_command=None)

# Diccionario de colas por servidor
queues = {}

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = MusicQueue()
    return queues[guild_id]

async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    
    if not queue.songs:
        queue.is_playing = False
        return

    song_info = queue.get_next()
    
    try:
        player = await YTDLSource.from_url(song_info['url'], loop=bot.loop, stream=True)
        queue.current = player
        
        def after_playing(error):
            if error:
                print(f'❌ Error del reproductor: {error}')
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        
        queue.voice_client.play(player, after=after_playing)
        queue.is_playing = True
        
        embed = discord.Embed(
            title="🎵 Reproduciendo ahora",
            description=f"[{player.title}]({player.webpage_url})",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=player.thumbnail)
        embed.add_field(name="Duración", value=player.duration, inline=True)
        embed.add_field(name="Solicitado por", value=song_info['requester'], inline=True)
        embed.timestamp = discord.utils.utcnow()
        
        await queue.text_channel.send(embed=embed)
        
    except Exception as e:
        print(f'❌ Error al reproducir: {e}')
        await queue.text_channel.send('❌ Error al reproducir la canción.')
        await play_next(ctx)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')
    print(f'🎵 Servidor(es): {len(bot.guilds)}')
    print(f'👥 Usuarios: {len(bot.users)}')
    print(f'📝 Usa {config["prefix"]}help para ver los comandos')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'música | {config["prefix"]}help'))

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, query: str):
    """Reproduce una canción de YouTube"""
    
    if not ctx.author.voice:
        return await ctx.reply('❌ Debes estar en un canal de voz.')
    
    voice_channel = ctx.author.voice.channel
    queue = get_queue(ctx.guild.id)
    
    # Conectar al canal de voz si no está conectado
    if not queue.voice_client or not queue.voice_client.is_connected():
        queue.voice_client = await voice_channel.connect()
        queue.text_channel = ctx.channel
    
    await ctx.send('🔍 Buscando...')
    
    try:
        # Buscar información del video
        loop = bot.loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False))
        
        if 'entries' in data:
            if not data['entries']:
                return await ctx.send('❌ No se encontraron resultados.')
            data = data['entries'][0]
        
        song_info = {
            'url': data['webpage_url'],
            'title': data['title'],
            'thumbnail': data.get('thumbnail'),
            'duration': YTDLSource.format_duration(data.get('duration', 0)),
            'requester': ctx.author.mention
        }
        
        queue.add_song(song_info)
        
        # Si no está reproduciendo, empezar
        if not queue.is_playing:
            await play_next(ctx)
        else:
            embed = discord.Embed(
                title="➕ Añadido a la cola",
                description=f"[{song_info['title']}]({song_info['url']})",
                color=discord.Color.yellow()
            )
            embed.set_thumbnail(url=song_info['thumbnail'])
            embed.add_field(name="Posición", value=str(len(queue.songs)), inline=True)
            embed.add_field(name="Duración", value=song_info['duration'], inline=True)
            embed.add_field(name="Solicitado por", value=song_info['requester'], inline=True)
            embed.timestamp = discord.utils.utcnow()
            
            await ctx.send(embed=embed)
            
    except Exception as e:
        print(f'❌ Error: {e}')
        await ctx.send('❌ Error al procesar el video.')

@bot.command(name='pause')
async def pause(ctx):
    """Pausa la reproducción"""
    queue = get_queue(ctx.guild.id)
    
    if queue.voice_client and queue.voice_client.is_playing():
        queue.voice_client.pause()
        await ctx.message.add_reaction('⏸️')
    else:
        await ctx.reply('❌ No hay nada reproduciéndose.')

@bot.command(name='resume', aliases=['r'])
async def resume(ctx):
    """Reanuda la reproducción"""
    queue = get_queue(ctx.guild.id)
    
    if queue.voice_client and queue.voice_client.is_paused():
        queue.voice_client.resume()
        await ctx.message.add_reaction('▶️')
    else:
        await ctx.reply('❌ La música no está pausada.')

@bot.command(name='skip', aliases=['s'])
async def skip(ctx):
    """Salta a la siguiente canción"""
    queue = get_queue(ctx.guild.id)
    
    if queue.voice_client and (queue.voice_client.is_playing() or queue.voice_client.is_paused()):
        queue.voice_client.stop()
        await ctx.message.add_reaction('⏭️')
    else:
        await ctx.reply('❌ No hay nada reproduciéndose.')

@bot.command(name='stop')
async def stop(ctx):
    """Detiene la música y limpia la cola"""
    queue = get_queue(ctx.guild.id)
    
    if queue.voice_client:
        queue.songs.clear()
        queue.voice_client.stop()
        await queue.voice_client.disconnect()
        queue.voice_client = None
        queue.is_playing = False
        await ctx.message.add_reaction('⏹️')
    else:
        await ctx.reply('❌ No hay nada reproduciéndose.')

@bot.command(name='volume', aliases=['vol', 'v'])
async def volume(ctx, vol: int = None):
    """Ajusta el volumen (0-200)"""
    queue = get_queue(ctx.guild.id)
    
    if not queue.current:
        return await ctx.reply('❌ No hay nada reproduciéndose.')
    
    if vol is None:
        current_vol = int(queue.current.volume * 100)
        return await ctx.send(f'🔊 Volumen actual: **{current_vol}%**')
    
    if vol < 0 or vol > 200:
        return await ctx.reply('❌ El volumen debe estar entre 0 y 200.')
    
    queue.current.volume = vol / 100
    await ctx.send(f'🔊 Volumen ajustado a **{vol}%**')

@bot.command(name='queue', aliases=['q'])
async def show_queue(ctx):
    """Muestra la cola de reproducción"""
    queue = get_queue(ctx.guild.id)
    
    if not queue.songs and not queue.current:
        return await ctx.reply('❌ La cola está vacía.')
    
    embed = discord.Embed(
        title="📜 Cola de reproducción",
        color=discord.Color.blue()
    )
    
    description_lines = []
    
    # Canción actual
    if queue.current:
        description_lines.append(f"▶️ [{queue.current.title}]({queue.current.webpage_url}) - `{queue.current.duration}`")
    
    # Siguientes canciones
    for idx, song in enumerate(queue.songs[:9], start=1):
        description_lines.append(f"{idx}. [{song['title']}]({song['url']}) - `{song['duration']}`")
    
    embed.description = '\n'.join(description_lines)
    embed.set_footer(text=f"Total: {len(queue.songs) + (1 if queue.current else 0)} canción(es)")
    embed.timestamp = discord.utils.utcnow()
    
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Muestra la ayuda"""
    embed = discord.Embed(
        title="🎵 Comandos del Bot de Música",
        description="Lista de comandos disponibles:",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name=f"{config['prefix']}play <URL o nombre>",
        value="Reproduce una canción de YouTube (alias: !p)",
        inline=False
    )
    embed.add_field(
        name=f"{config['prefix']}pause",
        value="Pausa la reproducción actual",
        inline=False
    )
    embed.add_field(
        name=f"{config['prefix']}resume",
        value="Reanuda la reproducción (alias: !r)",
        inline=False
    )
    embed.add_field(
        name=f"{config['prefix']}skip",
        value="Salta a la siguiente canción (alias: !s)",
        inline=False
    )
    embed.add_field(
        name=f"{config['prefix']}stop",
        value="Detiene la música y limpia la cola",
        inline=False
    )
    embed.add_field(
        name=f"{config['prefix']}volume <0-200>",
        value="Ajusta el volumen (alias: !vol, !v)",
        inline=False
    )
    embed.add_field(
        name=f"{config['prefix']}queue",
        value="Muestra la cola de reproducción (alias: !q)",
        inline=False
    )
    embed.add_field(
        name=f"{config['prefix']}help",
        value="Muestra este mensaje de ayuda",
        inline=False
    )
    
    embed.set_footer(text="Bot de Música para Discord")
    embed.timestamp = discord.utils.utcnow()
    
    await ctx.send(embed=embed)

# Iniciar el bot
if __name__ == '__main__':
    bot.run(config['token'])
