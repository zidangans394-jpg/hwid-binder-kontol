import os
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import discord
from discord import app_commands
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

# ==================== BAGIAN BOT DISCORD ====================
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await init_db()
    await tree.sync()  # Sinkronisasi slash command ke Discord
    print(f"Bot {client.user} siap digunakan! Slash command sudah tersedia.")

@tree.command(name="bind", description="Mengikat license key dengan HWID")
@app_commands.describe(
    key="License key yang ingin di-bind",
    hwid="HWID komputer (opsional, kosongkan jika hanya ingin cek)"
)
async def bind(interaction: discord.Interaction, key: str, hwid: str = None):
    await interaction.response.defer(ephemeral=True)

    existing_hwid = await get_license(key)

    if existing_hwid is None:
        if hwid:
            await insert_license(key, hwid)
            await interaction.followup.send(
                f"✅ Key `{key}` berhasil di-bind dengan HWID `{hwid}`.",
                ephemeral=True
            )
        else:
            await insert_license(key, None)
            await interaction.followup.send(
                f"✅ Key `{key}` telah didaftarkan (tanpa HWID). Gunakan `/bind` lagi dengan HWID untuk mengikat.",
                ephemeral=True
            )
        return

    # Key sudah ada
    if existing_hwid is None:
        if hwid:
            await update_license_hwid(key, hwid)
            await interaction.followup.send(
                f"✅ Key `{key}` berhasil di-bind dengan HWID `{hwid}`.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"ℹ️ Key `{key}` sudah terdaftar tetapi belum di-bind. Silakan gunakan perintah dengan HWID.",
                ephemeral=True
            )
    else:
        if hwid:
            if hwid == existing_hwid:
                await interaction.followup.send(
                    f"🔒 Key `{key}` sudah ter-bind dengan HWID yang sama. (HWID: `{hwid}`)",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Key `{key}` sudah ter-bind dengan HWID berbeda. Hubungi admin jika ini adalah HWID baru Anda.",
                    ephemeral=True
                )
        else:
            await interaction.followup.send(
                f"🔒 Key `{key}` sudah ter-bind dengan HWID: `{existing_hwid}`",
                ephemeral=True
            )

# ==================== MENJALANKAN KEDUANYA ====================
def run_api():
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_api, daemon=True).start()
    client.run(os.getenv("DISCORD_TOKEN"))