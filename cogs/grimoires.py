import discord
from discord.ext import commands
import random
import json
from data.grimoire_list import LISTE_3_TREFLES, INFO_4_TREFLES

# --- CONFIGURATION DES DESTINS FORCÉS ---
ID_MODO_4_TREFLES = 1000243285337579671  # ID de Ientel -> 4 Trèfles
ID_MODO_SPECIFIQUE = 350798834181472257 # ID de Fubuki -> Son
ID_HAXXOR = 615902006493708308 # ID de Haxxor -> Ténèbres

GRIMOIRE_Son = "Son" # Le type que Fubuki recevra à 100%
GRIMOIRE_Tenebres = "Ténèbres" # Le type que Haxxor recevra à 100%

class Grimoires(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tirage(self, ctx):
        try:
            with open('database.json', 'r') as f:
                db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            db = {}

        user_id = ctx.author.id
        user_id_str = str(user_id)

        # 1. VERIFICATION : Le joueur a-t-il créé son identité ?
        if user_id_str not in db or "rp_name" not in db[user_id_str]:
            return await ctx.send("❌ **AYO ?!** T'es qui toi ?\nFais d'abord la commande `n!creation` pour te présenter (Nom + Photo).")

        # 2. VERIFICATION : A-t-il déjà un grimoire ?
        if "grimoire" in db[user_id_str]:
            embed_error = discord.Embed(
                title="📖 Destin Scellé",
                description=f"Désolé {ctx.author.mention}, ton grimoire t'accompagne déjà, il ne souhaite pas t'abandonner, enflure.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed_error)

        # 3. Logique des tirages forcés ou aléatoires
        res_db = None
        embed = None

        # CAS IENTEL : 4 Trèfles automatique
        if user_id == ID_MODO_4_TREFLES:
            embed = discord.Embed(
                title="🍀 MIRACLE : Le Quatrième Trèfle !",
                description=INFO_4_TREFLES["desc"],
                color=discord.Color.gold()
            )
            embed.set_image(url=INFO_4_TREFLES["img"])
            res_db = "4 Trèfles"

        # CAS FUBUKI : Élément spécifique (Fubuki -> Son)
        elif user_id == ID_MODO_SPECIFIQUE:
            element = GRIMOIRE_Son
            data = LISTE_3_TREFLES[element]
            embed = discord.Embed(
                title=f"☘️ Grimoire de type : {element}",
                description=data["desc"],
                color=discord.Color.blue()
            )
            embed.set_image(url=data["img"])
            res_db = element

        # CAS NORMAL : Aléatoire
        else:
            chance = random.randint(1, 100)
            if chance <= 5:
                embed = discord.Embed(
                    title="🍀 MIRACLE : Le Quatrième Trèfle !",
                    description=INFO_4_TREFLES["desc"],
                    color=discord.Color.gold()
                )
                embed.set_image(url=INFO_4_TREFLES["img"])
                res_db = "4 Trèfles"
            else:
                element = random.choice(list(LISTE_3_TREFLES.keys()))
                data = LISTE_3_TREFLES[element]
                couleurs = {"Feu": 0xFF0000, "Eau": 0x0000FF, "Vent": 0x00FF00, "Foudre": 0xA020F0, "Ténèbres": 0x2F3136}
                embed = discord.Embed(
                    title=f"☘️ Grimoire de type : {element}",
                    description=data["desc"],
                    color=couleurs.get(element, 0x333333)
                )
                embed.set_image(url=data["img"])
                res_db = element

        # 4. Sauvegarde
        db[user_id_str]["grimoire"] = res_db
        
        # On initialise les stats avec PV et Mana basés sur Endurance et Mana
        if "stats" not in db[user_id_str]:
            endurance = 10 # Base
            mana_stat = 10 # Base
            db[user_id_str]["stats"] = {
                "Physique": 10, "Magie": 10, "Defense": 10,
                "Vitesse": 10, "Mana": mana_stat, "Endurance": endurance,
                "Points_Libres": 50,
                "pv_max": 100 + (endurance * 10),
                "mana_max": 50 + (mana_stat * 5)
            
            }
        else:
            db[user_id_str]["stats"]["Points_Libres"] = 50

        with open('database.json', 'w') as f:
            json.dump(db, f, indent=4)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Grimoires(bot))