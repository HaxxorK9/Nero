import discord
from discord.ext import commands
import asyncio
import os

# Configuration des perms (Intents)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="n!", intents=intents)

# Fct pour charger les dossiers (Cogs)
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"✅ Module chargé : {filename}")
            except Exception as e:
                print(f"❌ Erreur sur {filename} : {e}")

async def main():
    async with bot:
        await load_extensions()
        # TOKEN
        await bot.start('TOKEN')

if __name__ == "__main__":
    asyncio.run(main())