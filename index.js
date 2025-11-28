const { Client, GatewayIntentBits, EmbedBuilder } = require('discord.js');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, AudioPlayerStatus, VoiceConnectionStatus } = require('@discordjs/voice');
const play = require('play-dl');
const config = require('./config.json');

// Crear cliente de Discord
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildVoiceStates
    ]
});

// Sistema de colas por servidor
const queues = new Map();

// Clase para manejar la cola de música
class MusicQueue {
    constructor(guildId, voiceChannel, textChannel) {
        this.guildId = guildId;
        this.voiceChannel = voiceChannel;
        this.textChannel = textChannel;
        this.songs = [];
        this.player = createAudioPlayer();
        this.connection = null;
        this.isPlaying = false;

        // Evento cuando termina una canción
        this.player.on(AudioPlayerStatus.Idle, () => {
            this.songs.shift();
            if (this.songs.length > 0) {
                this.playSong(this.songs[0]);
            } else {
                this.isPlaying = false;
            }
        });

        // Evento de error
        this.player.on('error', error => {
            console.error('❌ Error del reproductor:', error);
            this.textChannel.send('❌ Error al reproducir la canción.');
            this.songs.shift();
            if (this.songs.length > 0) {
                this.playSong(this.songs[0]);
            }
        });
    }

    async addSong(song) {
        this.songs.push(song);

        if (!this.connection) {
            this.connection = joinVoiceChannel({
                channelId: this.voiceChannel.id,
                guildId: this.guildId,
                adapterCreator: this.voiceChannel.guild.voiceAdapterCreator,
            });

            this.connection.on(VoiceConnectionStatus.Disconnected, () => {
                this.connection = null;
                queues.delete(this.guildId);
            });

            this.connection.subscribe(this.player);
        }

        if (this.songs.length === 1) {
            await this.playSong(song);
        } else {
            const embed = new EmbedBuilder()
                .setColor('#ffff00')
                .setTitle('➕ Añadido a la cola')
                .setDescription(`[${song.title}](${song.url})`)
                .setThumbnail(song.thumbnail)
                .addFields(
                    { name: 'Posición', value: `${this.songs.length}`, inline: true },
                    { name: 'Duración', value: song.duration, inline: true },
                    { name: 'Solicitado por', value: song.requestedBy, inline: true }
                )
                .setTimestamp();
            
            this.textChannel.send({ embeds: [embed] });
        }
    }

    async playSong(song) {
        try {
            const stream = await play.stream(song.url);
            const resource = createAudioResource(stream.stream, {
                inputType: stream.type
            });

            this.player.play(resource);
            this.isPlaying = true;

            const embed = new EmbedBuilder()
                .setColor('#00ff00')
                .setTitle('🎵 Reproduciendo ahora')
                .setDescription(`[${song.title}](${song.url})`)
                .setThumbnail(song.thumbnail)
                .addFields(
                    { name: 'Duración', value: song.duration, inline: true },
                    { name: 'Solicitado por', value: song.requestedBy, inline: true }
                )
                .setTimestamp();
            
            this.textChannel.send({ embeds: [embed] });
        } catch (error) {
            console.error('❌ Error al reproducir:', error);
            this.textChannel.send('❌ Error al reproducir la canción.');
        }
    }

    skip() {
        this.player.stop();
    }

    stop() {
        this.songs = [];
        this.player.stop();
        if (this.connection) {
            this.connection.destroy();
            this.connection = null;
        }
        queues.delete(this.guildId);
    }

    pause() {
        return this.player.pause();
    }

    resume() {
        return this.player.unpause();
    }
}

// Evento: Bot listo
client.once('ready', () => {
    console.log(`✅ Bot conectado como ${client.user.tag}`);
    console.log(`🎵 Servidor(es): ${client.guilds.cache.size}`);
    console.log(`👥 Usuarios: ${client.users.cache.size}`);
    console.log(`📝 Usa ${config.prefix}help para ver los comandos`);
    client.user.setActivity('música | !help', { type: 2 });
});

// Evento: Mensaje recibido
client.on('messageCreate', async message => {
    if (message.author.bot) return;
    if (!message.content || !message.content.startsWith(config.prefix)) return;

    const args = message.content.slice(config.prefix.length).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    console.log(`🎵 Comando: ${command} | Usuario: ${message.author.tag}`);

    // Comandos
    if (command === 'play' || command === 'p') {
        const voiceChannel = message.member.voice.channel;
        if (!voiceChannel) {
            return message.reply('❌ Debes estar en un canal de voz.');
        }

        const query = args.join(' ');
        if (!query) {
            return message.reply('❌ Proporciona un enlace o nombre de canción de YouTube.');
        }

        try {
            message.channel.send('🔍 Buscando...');

            // Buscar en YouTube
            let videoInfo;
            if (play.yt_validate(query) === 'video') {
                videoInfo = await play.video_info(query);
            } else {
                const searched = await play.search(query, { limit: 1 });
                if (searched.length === 0) {
                    return message.reply('❌ No se encontraron resultados.');
                }
                videoInfo = await play.video_info(searched[0].url);
            }

            const song = {
                title: videoInfo.video_details.title,
                url: videoInfo.video_details.url,
                duration: formatDuration(videoInfo.video_details.durationInSec),
                thumbnail: videoInfo.video_details.thumbnails[0].url,
                requestedBy: message.author.tag
            };

            // Obtener o crear cola
            let queue = queues.get(message.guild.id);
            if (!queue) {
                queue = new MusicQueue(message.guild.id, voiceChannel, message.channel);
                queues.set(message.guild.id, queue);
            }

            await queue.addSong(song);

        } catch (error) {
            console.error('❌ Error:', error);
            message.reply('❌ Error al procesar el video.');
        }
    }
    else if (command === 'skip' || command === 's') {
        const queue = queues.get(message.guild.id);
        if (!queue || queue.songs.length === 0) {
            return message.reply('❌ No hay nada reproduciéndose.');
        }
        
        queue.skip();
        message.react('⏭️');
    }
    else if (command === 'stop') {
        const queue = queues.get(message.guild.id);
        if (!queue) {
            return message.reply('❌ No hay nada reproduciéndose.');
        }
        
        queue.stop();
        message.react('⏹️');
    }
    else if (command === 'pause') {
        const queue = queues.get(message.guild.id);
        if (!queue || !queue.isPlaying) {
            return message.reply('❌ No hay nada reproduciéndose.');
        }
        
        if (queue.pause()) {
            message.react('⏸️');
        } else {
            message.reply('❌ Ya está pausado.');
        }
    }
    else if (command === 'resume' || command === 'r') {
        const queue = queues.get(message.guild.id);
        if (!queue) {
            return message.reply('❌ No hay nada reproduciéndose.');
        }
        
        if (queue.resume()) {
            message.react('▶️');
        } else {
            message.reply('❌ Ya está reproduciéndose.');
        }
    }
    else if (command === 'queue' || command === 'q') {
        const queue = queues.get(message.guild.id);
        if (!queue || queue.songs.length === 0) {
            return message.reply('❌ La cola está vacía.');
        }

        const embed = new EmbedBuilder()
            .setColor('#0099ff')
            .setTitle('📜 Cola de reproducción')
            .setDescription(
                queue.songs.map((song, id) => 
                    `${id === 0 ? '▶️' : `${id}.`} [${song.title}](${song.url}) - \`${song.duration}\``
                ).slice(0, 10).join('\n')
            )
            .setFooter({ text: `Total: ${queue.songs.length} canción(es)` })
            .setTimestamp();

        message.channel.send({ embeds: [embed] });
    }
    else if (command === 'help') {
        const embed = new EmbedBuilder()
            .setColor('#9b59b6')
            .setTitle('🎵 Comandos del Bot de Música')
            .setDescription('Lista de comandos disponibles:')
            .addFields(
                { name: `${config.prefix}play <URL o nombre>`, value: 'Reproduce una canción de YouTube (alias: !p)', inline: false },
                { name: `${config.prefix}pause`, value: 'Pausa la reproducción actual', inline: false },
                { name: `${config.prefix}resume`, value: 'Reanuda la reproducción (alias: !r)', inline: false },
                { name: `${config.prefix}skip`, value: 'Salta a la siguiente canción (alias: !s)', inline: false },
                { name: `${config.prefix}stop`, value: 'Detiene la música y limpia la cola', inline: false },
                { name: `${config.prefix}queue`, value: 'Muestra la cola de reproducción (alias: !q)', inline: false },
                { name: `${config.prefix}help`, value: 'Muestra este mensaje de ayuda', inline: false }
            )
            .setFooter({ text: 'Bot de Música para Discord' })
            .setTimestamp();

        message.channel.send({ embeds: [embed] });
    }
});

// Función auxiliar para formatear duración
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

// Iniciar sesión del bot
client.login(config.token);
