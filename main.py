import os
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import discord
from discord.ext import commands
import aiosqlite
from database import init_db, get_license, insert_license, update_license_hwid

# ==================== BAGIAN API ====================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
)

@app.get("/")
async def root():
    return {"status": "API is running"}

@app.get("/verify")
async def verify(key: str, hwid: str):
    async with aiosqlite.connect("licenses.db") as db:
        cursor = await db.execute("SELECT hwid FROM licenses WHERE key = ?", (key,))
        row = await cursor.fetchone()
        if row and row[0] == hwid:
            return {"success": True}
        else:
            return {"success": False}

# ==================== BAGIAN BOT ====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await init_db()
    print(f"Bot {bot.user} siap digunakan!")

@bot.command(name="bind")
async def bind(ctx, key: str, hwid: str = None):
    # Ambil data dari database
    existing_hwid = await get_license(key)

    if existing_hwid is None:
        if hwid:
            await insert_license(key, hwid)
            await ctx.send(f"✅ Key `{key}` berhasil di-bind dengan HWID `{hwid}`.")
        else:
            await insert_license(key, None)
            await ctx.send(f"✅ Key `{key}` telah didaftarkan (tanpa HWID). Gunakan `!bind {key} HWID` untuk mengikat.")
        return

    if existing_hwid is None:
        if hwid:
            await update_license_hwid(key, hwid)
            await ctx.send(f"✅ Key `{key}` berhasil di-bind dengan HWID `{hwid}`.")
        else:
            await ctx.send(f"ℹ️ Key `{key}` sudah terdaftar tetapi belum di-bind. Silakan gunakan `!bind {key} HWID`.")
    else:
        if hwid:
            if hwid == existing_hwid:
                await ctx.send(f"🔒 Key `{key}` sudah ter-bind dengan HWID yang sama. (HWID: `{hwid}`)")
            else:
                await ctx.send(f"❌ Key `{key}` sudah ter-bind dengan HWID berbeda. Hubungi admin jika ini adalah HWID baru Anda.")
        else:
            await ctx.send(f"🔒 Key `{key}` sudah ter-bind dengan HWID: `{existing_hwid}`")

# ==================== MENJALANKAN KEDUANYA ====================
def run_api():
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Jalankan API di thread terpisah
    threading.Thread(target=run_api, daemon=True).start()
    # Jalankan bot
    bot.run(os.getenv("DISCORD_TOKEN"))