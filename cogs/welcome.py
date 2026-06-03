import discord
from discord.ext import commands
import json
import os

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database.json'

    def load_db(self):
        if not os.path.exists(self.db_path):
            return {}
        with open(self.db_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def save_db(self, db):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)

    @commands.Cog.listener()
    async def on_ready(self):
        """Synchronise uniquement les HUMAINS existants."""
        db = self.load_db()
        if "global_settings" not in db:
            db["global_settings"] = {"member_count_total": 0}
        
        guild = self.bot.guilds[0]
        # On filtre ici : seulement si member.bot est False
        humans = [m for m in guild.members if not m.bot]
        members = sorted(humans, key=lambda m: m.joined_at)

        changed = False
        for member in members:
            user_id = str(member.id)
            if user_id not in db:
                db[user_id] = {}
            
            if "member_number" not in db[user_id]:
                db["global_settings"]["member_count_total"] += 1
                db[user_id]["member_number"] = db["global_settings"]["member_count_total"]
                changed = True
        
        if changed:
            self.save_db(db)
            print(f"📊 Synchronisation terminée : {db['global_settings']['member_count_total']} humains enregistrés.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # SI C'EST UN BOT, ON S'ARRÊTE LÀ
        if member.bot:
            return

        db = self.load_db()
        user_id = str(member.id)
        
        if user_id not in db or "member_number" not in db[user_id]:
            if "global_settings" not in db:
                db["global_settings"] = {"member_count_total": 0}
            
            db["global_settings"]["member_count_total"] += 1
            member_number = db["global_settings"]["member_count_total"]
            
            if user_id not in db:
                db[user_id] = {}
            db[user_id]["member_number"] = member_number
            self.save_db(db)
        else:
            member_number = db[user_id]["member_number"]

        channel = self.bot.get_channel(1367533656788308149)
        
        if channel:
            embed = discord.Embed(
                title="Le destin d'un nouveau Chevalier-Mage s'éveille...",
                description=(
                    f"Il semblerait qu'un grimoire soit impatient de voir son porteur, pas vrai Marx ?\n"
                    f"Bienvenue à toi, {member.mention}."
                ),
                color=discord.Color.purple()
            )
            embed.set_image(url="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExbmt6a3cxbnd4czJjZzEweGEwdDZ1d3B1aXFzMnFqamVtemNvYWpleiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/5qCA0sK1V9GdI2KM3j/giphy.gif")
            embed.set_footer(text=f"Ientel presents | {member.guild.name} | Mage n°{member_number}")
            
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))