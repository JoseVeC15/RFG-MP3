# 🎵 Bot de Música para Discord

Bot de música completo para Discord con reproducción de YouTube, cola de canciones y controles avanzados. Optimizado para correr 24/7 en Replit con UptimeRobot.

## ✨ Características

- 🎵 Reproducción de música desde YouTube
- 🔍 Búsqueda por nombre o URL
- 📜 Sistema de cola de canciones
- ⏯️ Controles completos (play, pause, resume, skip, stop)
- 🔊 Control de volumen ajustable (0-200%)
- 🎨 Embeds bonitos con información de las canciones
- 🌐 Servidor web integrado para mantenerlo activo 24/7
- ⚡ Optimizado para alta calidad de audio (256kbps)

## 🚀 Despliegue Rápido en Replit

### Opción 1: Importar desde GitHub (Recomendado)

1. **Fork este repositorio** en GitHub
2. **Ve a Replit:** https://replit.com
3. **Click en:** "+ Create Repl"
4. **Selecciona:** "Import from GitHub"
5. **Pega la URL** de tu fork
6. **Click:** "Import from GitHub"

### Opción 2: Crear manualmente

1. Crea un nuevo Repl de Python en Replit
2. Sube los archivos: `main.py`, `requirements.txt`, `.replit`, `replit.nix`
3. Sigue los pasos de configuración abajo

## ⚙️ Configuración en Replit

### 1. Configurar Secrets (Variables de Entorno)

En Replit, abre el panel de **Secrets** (🔒) y agrega:

| Key | Value |
|-----|-------|
| `DISCORD_TOKEN` | Tu token de Discord Bot |
| `PREFIX` | `!` (o el prefijo que prefieras) |

### 2. Obtener Token de Discord

1. Ve al [Discord Developer Portal](https://discord.com/developers/applications)
2. Crea una nueva aplicación o selecciona una existente
3. Ve a la sección **Bot**
4. Copia el **Token**
5. En **Privileged Gateway Intents**, activa:
   - ✅ Message Content Intent
   - ✅ Server Members Intent
   - ✅ Presence Intent

### 3. Invitar el Bot a tu Servidor

Usa este URL (reemplaza `CLIENT_ID` con tu Application ID):
```
https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=3165184&scope=bot
```

Permisos necesarios:
- Ver canales
- Enviar mensajes
- Conectar a voz
- Hablar

## 🌐 Mantener Activo 24/7 con UptimeRobot

### 1. Obtener URL del Repl

Cuando ejecutes el bot en Replit, copia la URL que aparece (ejemplo: `https://discordmusicbot.tuusuario.repl.co`)

### 2. Configurar UptimeRobot

1. Crea cuenta en [UptimeRobot](https://uptimerobot.com)
2. Click en **"+ Add New Monitor"**
3. Configura:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Discord Music Bot
   - **URL:** Tu URL de Replit
   - **Monitoring Interval:** 5 minutes
4. Click en **"Create Monitor"**

¡Listo! UptimeRobot hará ping cada 5 minutos para mantener el bot activo.

## 🎮 Comandos

| Comando | Alias | Descripción |
|---------|-------|-------------|
| `!play <URL o nombre>` | `!p` | Reproduce una canción de YouTube |
| `!pause` | - | Pausa la reproducción actual |
| `!resume` | `!r` | Reanuda la reproducción |
| `!skip` | `!s` | Salta a la siguiente canción |
| `!stop` | - | Detiene la música y limpia la cola |
| `!volume <0-200>` | `!vol`, `!v` | Ajusta el volumen |
| `!queue` | `!q` | Muestra la cola de reproducción |
| `!help` | - | Muestra la lista de comandos |

## 📦 Dependencias

- `discord.py` - API de Discord
- `yt-dlp` - Descarga de videos de YouTube
- `PyNaCl` - Soporte de audio para Discord
- `flask` - Servidor web para UptimeRobot

## 🔧 Configuración de Audio

El bot está optimizado para máxima calidad:
- **Bitrate:** 256kbps
- **Sample Rate:** 48kHz (estándar Discord)
- **Canales:** Estéreo
- **Buffer:** 2048k para evitar cortes
- **Ecualizador:** Mejora de graves

## 🛠️ Desarrollo Local

### Requisitos
- Python 3.8+
- FFmpeg instalado

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/tuusuario/discord-music-bot.git
cd discord-music-bot

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export DISCORD_TOKEN="tu_token_aqui"
export PREFIX="!"

# Ejecutar
python bot.py
```

## 📝 Estructura del Proyecto

```
discord-music-bot/
├── main.py              # Código principal del bot (para Replit)
├── bot.py              # Versión local (sin servidor web)
├── requirements.txt    # Dependencias de Python
├── .replit            # Configuración de Replit
├── replit.nix         # Dependencias del sistema (FFmpeg)
├── pyproject.toml     # Configuración del proyecto
├── .gitignore         # Archivos ignorados por Git
├── README.md          # Esta documentación
├── REPLIT-SETUP.md    # Guía detallada de Replit
└── CHANGELOG.md       # Registro de cambios
```

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m '✨ Add: AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

Ver `CONTRIBUTING.md` para más detalles.

## 📜 Licencia

Este proyecto está bajo la Licencia MIT.

## 🐛 Solución de Problemas

### El bot no se conecta
- Verifica que el token en Secrets sea correcto
- Asegúrate de que los Intents estén habilitados en Discord Developer Portal

### No reproduce música
- Verifica que FFmpeg esté instalado (automático en Replit)
- Asegúrate de estar en un canal de voz
- Revisa los logs en la consola de Replit

### El bot se desconecta
- Verifica que UptimeRobot esté configurado correctamente
- Asegúrate de que la URL de Replit sea correcta

## 📞 Soporte

Si tienes problemas:
1. Revisa la sección de solución de problemas
2. Busca en [Issues](https://github.com/tuusuario/discord-music-bot/issues)
3. Crea un nuevo Issue con detalles del problema

## ⭐ Agradecimientos

- [discord.py](https://github.com/Rapptz/discord.py)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Replit](https://replit.com)
- [UptimeRobot](https://uptimerobot.com)

---

Hecho con ❤️ para la comunidad de Discord

### Paso 4: Obtener Client ID

1. Ve a la sección **"General Information"**
2. Copia el **"Application ID"** (también llamado Client ID)

### Paso 5: Invitar el Bot a tu Servidor

1. Ve a la sección **"OAuth2"** > **"URL Generator"**
2. En **"Scopes"**, selecciona:
   - ✅ `bot`
   - ✅ `applications.commands`
3. En **"Bot Permissions"**, selecciona:
   - ✅ Send Messages
   - ✅ Send Messages in Threads
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Read Message History
   - ✅ Add Reactions
   - ✅ Connect
   - ✅ Speak
4. Copia la URL generada en la parte inferior
5. Pega la URL en tu navegador y selecciona tu servidor

## ⚙️ Instalación

### 1. Instalar Dependencias

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
npm install
```

### 2. Configurar el Bot

Abre el archivo `config.json` y reemplaza los valores:

```json
{
  "token": "TU_TOKEN_AQUI",
  "clientId": "TU_CLIENT_ID_AQUI",
  "prefix": "!"
}
```

- **token**: El token que copiaste en el Paso 2
- **clientId**: El Application ID que copiaste en el Paso 4
- **prefix**: El prefijo para los comandos (por defecto `!`)

## ▶️ Ejecutar el Bot

Para iniciar el bot, ejecuta:

```bash
npm start
```

Deberías ver el mensaje: `✅ Bot conectado como [NombreDelBot]#1234`

## 🎮 Comandos Disponibles

| Comando | Alias | Descripción |
|---------|-------|-------------|
| `!play <URL>` | `!p` | Reproduce una canción de YouTube |
| `!pause` | - | Pausa la reproducción actual |
| `!resume` | `!r` | Reanuda la reproducción |
| `!skip` | `!s` | Salta a la siguiente canción |
| `!stop` | - | Detiene la música y limpia la cola |
| `!queue` | `!q` | Muestra la cola de reproducción |
| `!help` | - | Muestra la lista de comandos |

## 📝 Ejemplos de Uso

```
!play https://www.youtube.com/watch?v=dQw4w9WgXcQ
!p https://www.youtube.com/watch?v=dQw4w9WgXcQ
!pause
!resume
!skip
!queue
!stop
```

## ⚠️ Solución de Problemas

### El bot no reproduce música

- Verifica que FFmpeg esté instalado correctamente
- Asegúrate de estar en un canal de voz
- Verifica que el enlace de YouTube sea válido

### Error de permisos

- Verifica que el bot tenga permisos de "Connect" y "Speak" en el canal de voz
- Revisa que hayas habilitado los Intents en el Developer Portal

### El bot no responde a comandos

- Verifica que hayas habilitado "MESSAGE CONTENT INTENT"
- Asegúrate de usar el prefijo correcto (por defecto `!`)

## 🛠️ Tecnologías Utilizadas

- **discord.js v14** - Librería principal de Discord
- **@discordjs/voice** - Manejo de audio
- **ytdl-core** - Descarga de audio de YouTube
- **ffmpeg-static** - Procesamiento de audio

## 📄 Licencia

MIT

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si encuentras algún error o tienes sugerencias, no dudes en abrir un issue.

---

**¡Disfruta de tu bot de música! 🎵**
