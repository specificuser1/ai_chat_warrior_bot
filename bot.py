import discord
from discord.ext import commands
from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROQ_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

MEMORY_FILE = "memory.json"

# ---------- MEMORY ----------

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

memory = load_memory()

# ---------- AI RESPONSE ----------

async def ai_reply(user_id, msg):

    history = memory.get(str(user_id), [])

    history.append({"role": "user", "content": msg})

    system_prompt = """
You are a friendly female AI chatbot.
Personality:
- Cute, friendly, helpful
- Speak English, Roman Urdu, Banglish
- Keep conversation safe and polite
"""

    try:
        chat = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role":"system","content":system_prompt}] + history[-10:]
        )

        reply = chat.choices[0].message.content

        history.append({"role": "assistant", "content": reply})
        memory[str(user_id)] = history[-20:]
        save_memory(memory)

        return reply

    except Exception as e:
        return "AI error 😅 thori der baad try karo."

# ---------- EVENTS ----------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ---------- STATUS COMMAND ----------

@bot.command()
async def status(ctx):
    embed = discord.Embed(title="🤖 AI Bot Status", color=0xff69b4)
    embed.add_field(name="AI", value="Online ✅")
    embed.add_field(name="Memory", value="Active ✅")
    embed.add_field(name="Languages", value="English / Roman Urdu / Banglish")
    embed.add_field(name="Channel Lock", value=f"<#{CHANNEL_ID}>")
    await ctx.send(embed=embed)

# ---------- CHAT ----------

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id != CHANNEL_ID:
        return

    if bot.user in message.mentions and "status" in message.content.lower():
        await message.channel.send("I'm online 💖 ready to chat!")
        return

    async with message.channel.typing():
        reply = await ai_reply(message.author.id, message.content)

    await message.reply(reply)
    await bot.process_commands(message)

# ---------- RUN ----------

bot.run(TOKEN)