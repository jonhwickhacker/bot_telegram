from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters
import datetime
import time
import json
import os

BOT_TOKEN = '7946021025:AAF2pvJw0haz4QH98Uv-R6werDlt8MSw97g'  # Reemplaza con tu token real
USUARIO_ID = '7195567580'    # Opcional: reemplaza con tu user_id si deseas restringirlo

# Archivo para guardar el historial de vasos
HISTORIAL_ARCHIVO = "historial_agua.json"

# Inicializar el historial si no existe
if not os.path.exists(HISTORIAL_ARCHIVO):
    with open(HISTORIAL_ARCHIVO, "w") as f:
        json.dump({}, f)

def cargar_historial():
    with open(HISTORIAL_ARCHIVO, "r") as f:
        return json.load(f)

def guardar_historial(historial):
    with open(HISTORIAL_ARCHIVO, "w") as f:
        json.dump(historial, f)

def registrar_toma(user_id):
    hoy = datetime.date.today().isoformat()
    historial = cargar_historial()
    if str(user_id) not in historial:
        historial[str(user_id)] = {}
    if hoy not in historial[str(user_id)]:
        historial[str(user_id)][hoy] = 0
    historial[str(user_id)][hoy] += 1
    guardar_historial(historial)

def obtener_registro_semanal(user_id):
    historial = cargar_historial()
    hoy = datetime.date.today()
    registros = []
    for i in range(7):
        dia = (hoy - datetime.timedelta(days=i)).isoformat()
        cantidad = historial.get(str(user_id), {}).get(dia, 0)
        registros.append(f"{dia}: {cantidad} vaso(s)")
    return "\n".join(reversed(registros))

# Botones principales
def crear_botones():
    botones = [
        [InlineKeyboardButton("✅ Ya tomé agua", callback_data="tomado")],
        [InlineKeyboardButton("⏳ Tiempo para el siguiente trago", callback_data="tiempo")],
        [InlineKeyboardButton("📊 ¿Cuántos vasos he tomado?", callback_data="historial")]
    ]
    return InlineKeyboardMarkup(botones)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu bot de hidratación. Te recordaré tomar agua cada 2 horas.",
        reply_markup=crear_botones()
    )

async def enviar_recordatorio(context: ContextTypes.DEFAULT_TYPE):
    hora_actual = datetime.datetime.now().time()
    if datetime.time(9, 0) <= hora_actual <= datetime.time(21, 0):
        await context.bot.send_message(
            chat_id=USUARIO_ID,
            text="¡Hora de tomar agua!",
            reply_markup=crear_botones()
        )

async def manejar_boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "tomado":
        registrar_toma(user_id)
        await query.edit_message_text("¡Bien hecho! Registrado tu vaso de agua.")
    elif query.data == "tiempo":
        ahora = datetime.datetime.now()
        proximo = ahora.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=2)
        if proximo.time() > datetime.time(21, 0):
            await query.edit_message_text("Ya no hay más recordatorios por hoy.")
        else:
            tiempo_restante = proximo - ahora
            minutos = tiempo_restante.seconds // 60
            await query.edit_message_text(f"Faltan {minutos} minutos para el siguiente recordatorio.")
    elif query.data == "historial":
        historial = obtener_registro_semanal(user_id)
        await query.edit_message_text(f"Tu historial de agua (últimos 7 días):\n\n{historial}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue = app.job_queue

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(CallbackQueryHandler(manejar_boton))

    print("Bot corriendo con recordatorios, botones y registro diario...")
    intervalo_segundos = 2 * 60 * 60  # cada 2 horas
    job_queue.run_repeating(enviar_recordatorio, interval=intervalo_segundos, first=0)
    app.run_polling() 
