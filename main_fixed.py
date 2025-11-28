import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os
from flask import Flask
from threading import Thread
import shutil
import glob
import traceback

# Cargar configuración desde variables de entorno (Replit Secrets)
TOKEN = os.environ.get('DISCORD_TOKEN')
PREFIX = os.environ.get('PREFIX', '!')

# Detectar FFmpeg (Replit usa Nix que lo instala en diferentes rutas)
FFMPEG_PATH = shutil.which('ffmpeg')
if not FFMPEG_PATH:
    print("⚠️ FFmpeg no encontrado en PATH, buscando en Nix store...")
    nix_paths = glob.glob('/nix/store/*/bin/ffmpeg')
    if nix_paths:
        FFMPEG_PATH = nix_paths[0]
        print(f"✅ FFmpeg encontrado en Nix: {FFMPEG_PATH}")
    else:
        for path in ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']:
            if os.path.exists(path):
                FFMPEG_PATH = path
                print(f"✅ FFmpeg encontrado en: {FFMPEG_PATH}")
                break

if FFMPEG_PATH:
    print(f"✅ Usando FFmpeg: {FFMPEG_PATH}")
else:
    print("❌ ADVERTENCIA: FFmpeg no encontrado - el audio no funcionará")

# Configuración de yt-dlp optimizada con bypass de detección
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'skip': ['hls', 'dash', 'translated_subs']
        }
    },
    'cookiesfrombrowser': None,
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -ar 48000 -ac 2'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# Flask app para mantener el bot activo (UptimeRobot)
app = Flask(__name__)

@app.route('/')
def home():
    return "🎵 Bot de Música está activo!"

@app.route('/ping')
def ping():
    return "pong"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.thumbnail = data.get('thumbnail')
        self.duration = self.format_duration(data.get('duration', 0))
        self.webpage_url = data.get('webpage_url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except Exception as e:
            print(f"❌ Error extrayendo info: {e}")
            traceback.print_exc()
            raise

        if data and 'entries' in data:
            data = data['entries'][0]
        
        if not data:
            raise ValueError("No se pudo extraer información de la canción")

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        print(f"🎵 Intentando reproducir: {data.get('title')}")
        print(f"📡 URL de stream: {filename[:100]}...")
        
        # Crear el audio source con FFmpeg
        try:
            if FFMPEG_PATH:
                audio_source = discord.FFmpegPCMAudio(
                    filename, 
                    executable=FFMPEG_PATH,
                    before_options=ffmpeg_options['before_options'],
                    options=ffmpeg_options['options']
                )
            else:
                audio_source = discord.FFmpegPCMAudio(
                    filename,
                    before_options=ffmpeg_options['before_options'],
                    options=ffmpeg_options['options']
                )
            
            return cls(audio_source, data=data)
        except Exception as e:
            print(f"❌ Error creando FFmpegPCMAudio: {e}")
            traceback.print_exc()
            raise

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

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

queues = {}

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = MusicQueue()
    return queues[guild_id]

async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    
    if not queue.songs:
        queue.is_playing = False
        print("📭 Cola vacía, deteniendo reproducción")
        return

    song_info = queue.get_next()
    print(f"▶️ Reproduciendo siguiente: {song_info['title']}")
    
    try:
        player = await YTDLSource.from_url(song_info['url'], loop=bot.loop, stream=True)
        queue.current = player
        
        def after_playing(error):
            if error:
                print(f'❌ Error del reproductor: {error}')
                traceback.print_exc()
            else:
                print(f"✅ Terminó de reproducir: {song_info['title']}")
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
        print(f'❌ Error crítico al reproducir: {e}')
        traceback.print_exc()
        await queue.text_channel.send(f'❌ Error al reproducir la canción: {str(e)}')
        await play_next(ctx)

@bot.event
async def on_ready():
    bot_name = bot.user.name if bot.user else 'Bot'
    print(f'✅ Bot conectado como {bot_name}')
    print(f'🎵 Servidor(es): {len(bot.guilds)}')
    print(f'👥 Usuarios: {len(bot.users)}')
    print(f'📝 Usa {PREFIX}help para ver los comandos')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'música | {PREFIX}help'))

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, query: str):
    """Reproduce una canción de YouTube"""
    
    if not ctx.author.voice:
        return await ctx.reply('❌ Debes estar en un canal de voz.')
    
    voice_channel = ctx.author.voice.channel
    queue = get_queue(ctx.guild.id)
    
    if not queue.voice_client or not queue.voice_client.is_connected():
        try:
            queue.voice_client = await voice_channel.connect()
            queue.text_channel = ctx.channel
            print(f"🔊 Conectado al canal de voz: {voice_channel.name}")
        except Exception as e:
            print(f"❌ Error conectando al canal de voz: {e}")
            return await ctx.send(f'❌ No pude conectarme al canal de voz: {str(e)}')
    
    searching_msg = await ctx.send('🔍 Buscando...')
    
    try:
        loop = bot.loop or asyncio.get_event_loop()
        print(f"🔍 Buscando: {query}")
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False))
        
        if not data:
            await searching_msg.delete()
            return await ctx.send('❌ No se pudo procesar la búsqueda.')
        
        if 'entries' in data:
            if not data['entries']:
                await searching_msg.delete()
                return await ctx.send('❌ No se encontraron resultados.')
            data = data['entries'][0]
        
        song_info = {
            'url': data['webpage_url'],
            'title': data['title'],
            'thumbnail': data.get('thumbnail'),
            'duration': YTDLSource.format_duration(data.get('duration', 0)),
            'requester': ctx.author.mention
        }
        
        print(f"✅ Canción encontrada: {song_info['title']}")
        queue.add_song(song_info)
        
        await searching_msg.delete()
        
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
        print(f'❌ Error en comando play: {e}')
        traceback.print_exc()
        await searching_msg.delete()
        await ctx.send(f'❌ Error al procesar: {str(e)}')

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

@bot.command(name='skip', aliases=['s', 'next'])
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
async def volume(ctx, vol: int | None = None):
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
    
    if queue.current:
        description_lines.append(f"▶️ [{queue.current.title}]({queue.current.webpage_url}) - `{queue.current.duration}`")
    
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
        name=f"{PREFIX}play <URL o nombre>",
        value="Reproduce una canción de YouTube (alias: !p)",
        inline=False
    )
    embed.add_field(
        name=f"{PREFIX}pause",
        value="Pausa la reproducción actual",
        inline=False
    )
    embed.add_field(
        name=f"{PREFIX}resume",
        value="Reanuda la reproducción (alias: !r)",
        inline=False
    )
    embed.add_field(
        name=f"{PREFIX}skip",
        value="Salta a la siguiente canción (alias: !s, !next)",
        inline=False
    )
    embed.add_field(
        name=f"{PREFIX}stop",
        value="Detiene la música y limpia la cola",
        inline=False
    )
    embed.add_field(
        name=f"{PREFIX}volume <0-200>",
        value="Ajusta el volumen (alias: !vol, !v)",
        inline=False
    )
    embed.add_field(
        name=f"{PREFIX}queue",
        value="Muestra la cola de reproducción (alias: !q)",
        inline=False
    )
    embed.add_field(
        name=f"{PREFIX}help",
        value="Muestra este mensaje de ayuda",
        inline=False
    )
    
    embed.set_footer(text="Bot de Música para Discord")
    embed.timestamp = discord.utils.utcnow()
    
    await ctx.send(embed=embed)

if __name__ == '__main__':
    if not TOKEN:
        print("❌ ERROR: No se encontró DISCORD_TOKEN en las variables de entorno")
        print("Por favor, configura DISCORD_TOKEN en Replit Secrets")
        exit(1)
    
    keep_alive()  # Inicia el servidor web para UptimeRobot
    bot.run(TOKEN)
