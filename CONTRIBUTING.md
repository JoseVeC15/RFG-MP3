# 🤝 Guía de Contribución

¡Gracias por tu interés en contribuir al Bot de Música para Discord! 🎵

## 📋 Cómo Contribuir

### 1. Reportar Errores

Si encuentras un error:
- Verifica que no esté ya reportado
- Describe claramente el problema
- Incluye pasos para reproducirlo
- Especifica tu entorno (Node.js version, OS, etc.)

### 2. Sugerir Mejoras

Para nuevas características:
- Explica claramente la funcionalidad deseada
- Describe casos de uso
- Considera la compatibilidad con el código existente

### 3. Enviar Pull Requests

**Pasos:**

1. Haz fork del repositorio
2. Crea una rama para tu característica:
   ```bash
   git checkout -b feature/nueva-caracteristica
   ```
3. Realiza tus cambios
4. Asegúrate de que el código funcione
5. Commit con mensajes descriptivos en español:
   ```bash
   git commit -m "✨ Añadir: [descripción]"
   ```
6. Push a tu fork:
   ```bash
   git push origin feature/nueva-caracteristica
   ```
7. Abre un Pull Request

## 📝 Estándares de Código

### Mensajes de Commit

Usa prefijos emoji para claridad:

- `✨ Añadir:` - Nueva característica
- `🐛 Corregir:` - Corrección de error
- `📝 Docs:` - Cambios en documentación
- `♻️ Refactor:` - Refactorización de código
- `🎨 Estilo:` - Formateo, espacios, etc.
- `⚡ Mejorar:` - Mejora de rendimiento
- `🔧 Config:` - Cambios de configuración
- `🧪 Test:` - Añadir o actualizar tests

**Ejemplo:**
```bash
git commit -m "✨ Añadir: comando de volumen para controlar audio"
```

### Estilo de Código

- Usa español para comentarios y mensajes
- Indentación: 4 espacios
- Nombres de variables descriptivos en español
- Funciones con verbos en infinitivo (ej: `reproducirCancion`)
- Constantes en MAYÚSCULAS_CON_GUION

### Estructura de Funciones

```javascript
// Comando: Descripción clara
async function nombreComando(message, args) {
    // Validaciones primero
    if (!validacion) {
        return message.reply('❌ Mensaje de error claro');
    }

    try {
        // Lógica principal
        // Código limpio y comentado
        
    } catch (error) {
        console.error('❌ Error:', error);
        return message.reply('❌ Mensaje de error al usuario');
    }
}
```

## 🧪 Testing

Antes de enviar un PR:
- [ ] El bot inicia sin errores
- [ ] Todos los comandos funcionan correctamente
- [ ] No hay errores en la consola
- [ ] El código está comentado apropiadamente
- [ ] La documentación está actualizada

## 📚 Documentación

Si tu cambio afecta el uso del bot:
- Actualiza el README.md
- Actualiza el comando !help si es necesario
- Añade ejemplos de uso
- Documenta en CHANGELOG.md

## 🌍 Idioma

- **Código**: Comentarios en español
- **Commits**: Mensajes en español
- **Documentación**: Completamente en español
- **Mensajes de usuario**: En español

## ❓ Preguntas

Si tienes dudas sobre cómo contribuir, no dudes en preguntar abriendo un issue.

---

**¡Gracias por hacer este proyecto mejor! 🎉**
