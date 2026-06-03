import discord
from discord.ext import commands
import json
import random

# --- RÉÉQUILIBRAGE DES COÛTS ---
MAGIC_TIERS = {
    "D": {"cout": 30, "bonus": 10, "nom": "Sort Mineur"},
    "C": {"cout": 85, "bonus": 30, "nom": "Sort Intermédiaire"},
    "B": {"cout": 150, "bonus": 70, "nom": "Sort Avancé"},
    "A": {"cout": 250, "bonus": 150, "nom": "Sort Ultime"}
}

class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.combats_actifs = {}

    def load_db(self):
        try:
            with open('database.json', 'r') as f:
                return json.load(f)
        except: return {}

    @commands.command(name="duel")
    async def duel(self, ctx, cible: discord.Member):
        if cible == ctx.author: return await ctx.send("Tu ne peux pas te battre contre toi-même.")
        
        db = self.load_db()
        p1_id, p2_id = str(ctx.author.id), str(cible.id)

        if p1_id not in db or p2_id not in db:
            return await ctx.send("❌ L'un des deux n'a pas de fiche perso.")

        s1, s2 = db[p1_id]["stats"], db[p2_id]["stats"]
        
        # Endurance x5 pour éviter les sacs de PV
        hp_p1 = 100 + (s1.get("Endurance", 0) * 5)
        hp_p2 = 100 + (s2.get("Endurance", 0) * 5)
        mana_p1 = 50 + (s1.get("Mana", 0) * 5)
        mana_p2 = 50 + (s2.get("Mana", 0) * 5)

        v1, v2 = s1.get("Vitesse", 0), s2.get("Vitesse", 0)
        if v1 > v2: premier = ctx.author.id
        elif v2 > v1: premier = cible.id
        else: premier = random.choice([ctx.author.id, cible.id])

        self.combats_actifs[ctx.channel.id] = {
            "p1": ctx.author.id,
            "p2": cible.id,
            "stats": {
                ctx.author.id: {"hp": hp_p1, "mana": mana_p1, "vit": v1},
                cible.id: {"hp": hp_p2, "mana": mana_p2, "vit": v2}
            },
            "tour": premier,
            "actions_faites": 0
        }

        await ctx.send(f"# ⚔️ **LE DUEL COMMENCE !**\n{ctx.author.mention} ({hp_p1} HP) 🆚 {cible.mention} ({hp_p2} HP)\nDébut : <@{premier}>")

    @commands.command(name="attaque")
    async def attaque(self, ctx, type_attaque: str, rang: str = None):
        channel_id = ctx.channel.id
        if channel_id not in self.combats_actifs:
            return await ctx.send("❌ Aucun combat ici.")

        combat = self.combats_actifs[channel_id]
        if ctx.author.id != combat["tour"]:
            return await ctx.send(f"✋ Tour de <@{combat['tour']}>.")

        att_id = ctx.author.id
        def_id = combat["p2"] if att_id == combat["p1"] else combat["p1"]
        
        s_att = combat["stats"][att_id]
        s_def = combat["stats"][def_id]
        db = self.load_db()
        db_att, db_def = db[str(att_id)]["stats"], db[str(def_id)]["stats"]

        degats_bruts = 0
        if type_attaque.lower() == "physique":
            degats_bruts = db_att.get("Physique", 0) * 1.0
        elif type_attaque.lower() == "magie":
            if not rang or rang.upper() not in MAGIC_TIERS:
                return await ctx.send("Précise le rang : D, C, B, A.")
            info = MAGIC_TIERS[rang.upper()]
            if s_att["mana"] < info["cout"]:
                return await ctx.send(f"💧 Mana insuffisant ({s_att['mana']}/{info['cout']}) !")
            s_att["mana"] -= info["cout"]
            degats_bruts = (db_att.get("Magie", 0) * 1.5) + info["bonus"]

        # --- NOUVELLE RÈGLE ESQUIVE (x3 Vitesse) ---
        chance_esquive = 20 if s_def["vit"] >= (s_att["vit"] * 3) else 0
        
        if chance_esquive > 0 and random.randint(1, 100) <= chance_esquive:
            degats_finaux = 0
            resultat_txt = "🍃 **ESQUIVE !** L'attaque n'a rien touché !"
        else:
            reduction = db_def.get("Defense", 0) / 3
            degats_finaux = max(0, int(degats_bruts - reduction))
            s_def["hp"] -= degats_finaux
            resultat_txt = f"💥 **{degats_finaux} dégâts** infligés !"

        # Sécurité affichage HP
        hp_visuel = max(0, s_def["hp"])
        cible_user = await self.bot.fetch_user(def_id)
        
        embed = discord.Embed(title="⚔️ Action de Combat", color=discord.Color.red())
        embed.add_field(name=ctx.author.display_name, value=f"❤️ {s_att['hp']} | 🌀 {s_att['mana']}")
        embed.add_field(name=cible_user.display_name, value=f"❤️ {hp_visuel} | {resultat_txt}")
        await ctx.send(embed=embed)

        if s_def["hp"] <= 0:
            await ctx.send(f"🏆 {ctx.author.mention} remporte le duel !")
            del self.combats_actifs[channel_id]
            return

        # --- NOUVELLE RÈGLE BLITZ (x3 Vitesse) ---
        combat["actions_faites"] += 1
        max_actions = 2 if s_att["vit"] >= (s_def["vit"] * 3) else 1
        
        if combat["actions_faites"] >= max_actions:
            combat["tour"] = def_id
            combat["actions_faites"] = 0
            await ctx.send(f"🔄 Tour de <@{def_id}> !")
        else:
            await ctx.send(f"⚡ **BLITZ !** Ta vitesse est fulgurante, encore 1 action !")

async def setup(bot):
    await bot.add_cog(Combat(bot))