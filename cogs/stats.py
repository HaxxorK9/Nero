import discord
from discord.ext import commands
import json
import asyncio # Nécessaire pour attendre les réponses du joueur
from radar_stats import generate_stats_image
import os

ID_SALON_LOGS = 1461477213034516551 

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_db(self):
        try:
            with open('database.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_db(self, db):
        with open('database.json', 'w') as f:
            json.dump(db, f, indent=4)

    # --- LOGS AUTOMATIQUES POUR CHAQUE COMMANDE ---
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Détecte quand n'importe quelle commande est tapée et l'envoie dans les logs."""
        if ctx.cog == self: # On ne logue que les commandes de ce fichier (stats.py)
            log_channel = self.bot.get_channel(ID_SALON_LOGS)
            if log_channel:
                await log_channel.send(f"📑 **LOG** | `{ctx.author}` a utilisé la commande : `{ctx.message.content}`")

    # --- COMMANDE INTERACTIVE : CRÉATION DU PERSONNAGE ---
    @commands.command(name="creation")
    async def create_character(self, ctx):
        """Lance la procédure de création de personnage (Nom + Image uploadée)."""
        db = self.load_db()
        user_id = str(ctx.author.id)

        # 1. Demande du NOM
        await ctx.send(f"👋 Bienvenue {ctx.author.mention}. Commençons ton inscription.\n**Quel est le nom de ton personnage RP ?**")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg_nom = await self.bot.wait_for('message', check=check, timeout=60.0)
            nom_rp = msg_nom.content
        except asyncio.TimeoutError:
            return await ctx.send("⏱️ Trop lent ! La création est annulée. Relance `n!creation`.")

        # 2. Demande de l'IMAGE (Upload)
        await ctx.send(f"C'est noté **{nom_rp}**.\nMaintenant, **envoie une image** de ton personnage directement ici.")

        try:
            while True:
                msg_img = await self.bot.wait_for('message', check=check, timeout=120.0)
                if msg_img.attachments:
                    url_image = msg_img.attachments[0].url
                    break
                else:
                    await ctx.send("❌ Envoie une image en pièce jointe (upload).")
        except asyncio.TimeoutError:
            return await ctx.send("⏱️ Trop lent ! Création annulée.")

        if user_id not in db:
            db[user_id] = {}

        db[user_id]["rp_name"] = nom_rp
        db[user_id]["rp_avatar"] = url_image
        self.save_db(db)

        embed = discord.Embed(
            title="✨ Identité Enregistrée",
            description=f"Ton personnage **{nom_rp}** est prêt.\n\n➡️ **Prochaine étape :** `n!tirage`.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=url_image)
        await ctx.send(embed=embed)

    @commands.command(name="stats")
    async def show_stats(self, ctx, member: discord.Member = None):

        member = member or ctx.author

        db = self.load_db()
        user_id = str(member.id)

        if user_id not in db:
            return await ctx.send(
                "❌ Profil introuvable. Fais `n!creation` d'abord."
            )

        # --- Récupération des données ---
        s = db[user_id].get("stats", {})

        nom_rp = db[user_id].get(
            "rp_name",
            member.display_name
        )

        img_rp = db[user_id].get(
            "rp_avatar",
            member.display_avatar.url
        )

        grimoire = db[user_id].get(
            "grimoire",
            "Aucun"
        )

        # --- Stats radar ---
        radar_stats = {
            "Physique": s.get("Physique", 0),
            "Magie": s.get("Magie", 0),
            "Défense": s.get("Defense", 0),
            "Vitesse": s.get("Vitesse", 0),
            "Mana": s.get("Mana", 0),
            "Endurance": s.get("Endurance", 0)
        }

        # --- Nom image temporaire ---
        image_path = f"stats_{member.id}.png"

        # --- Génération radar ---
        generate_stats_image(
            radar_stats,
            nom_rp,
            image_path
        )

        # --- Création fichier Discord ---
        file = discord.File(
            image_path,
            filename="stats.png"
        )

        # --- Embed Discord ---
        embed = discord.Embed(
            title=f"📊 Registre : {nom_rp}",
            description=(
                f"⚔️ **Grimoire :** {grimoire}\n"
                f"✨ **Points disponibles :** "
                f"{s.get('Points_Libres', 0)}"
            ),
            color=discord.Color.orange()
        )

        embed.set_thumbnail(url=img_rp)

        # IMPORTANT :
        # on affiche l'image générée
        embed.set_image(url="attachment://stats.png")

        embed.set_footer(
            text="Nero ne vous quitte pas des yeux."
        )

        # --- Envoi ---
        await ctx.send(
            embed=embed,
            file=file
        )

        # --- Nettoyage image ---
        if os.path.exists(image_path):
            os.remove(image_path)

    @commands.command(name="repartir")
    async def repartir_stats(self, ctx, points: int, stat_name: str):
        """Répartition des points + Log."""
        db = self.load_db()
        user_id = str(ctx.author.id)
        
        if user_id not in db or "stats" not in db[user_id]: 
            return await ctx.send("❌ Tu n'as pas de stats.")
        
        s = db[user_id]["stats"]
        valid_stats = ["Physique", "Magie", "Defense", "Vitesse", "Mana", "Endurance"]
        stat_target = stat_name.capitalize()
        if stat_target == "Défense": stat_target = "Defense"

        if stat_target not in valid_stats or points <= 0:
            return await ctx.send("❌ Statistique invalide.")

        if s.get("Points_Libres", 0) < points:
            return await ctx.send(f"❌ Points insuffisants.")

        s["Points_Libres"] -= points
        s[stat_target] += points
        self.save_db(db)
        
        await ctx.send(f"✅ Tu as ajouté **{points}** points en **{stat_target}**.")

        log_channel = self.bot.get_channel(ID_SALON_LOGS)
        if log_channel:
            nom_rp = db[user_id].get("rp_name", ctx.author.name)
            log_embed = discord.Embed(title="📈 Répartition", description=f"**{nom_rp}** a mis +{points} en {stat_target}.", color=discord.Color.green())
            await log_channel.send(embed=log_embed)

    # --- AJOUT ET RETRAIT (ADMINS) ---

    @commands.command(name="stats_add")
    @commands.has_permissions(administrator=True)
    async def add_points_libres(self, ctx, member: discord.Member, points: int):
        db = self.load_db()
        user_id = str(member.id)
        if user_id not in db: return await ctx.send("❌ Profil introuvable.")
        if "stats" not in db[user_id]: db[user_id]["stats"] = {"Points_Libres": 0}

        db[user_id]["stats"]["Points_Libres"] += points
        self.save_db(db)
        await ctx.send(f"🎁 {member.mention} a reçu **{points}** points !")

        log_channel = self.bot.get_channel(ID_SALON_LOGS)
        if log_channel:
            embed = discord.Embed(title="🎁 Ajout Admin", description=f"**Modo :** {ctx.author}\n**Cible :** {member}\n**Montant :** +{points}", color=discord.Color.gold())
            await log_channel.send(embed=embed)

    @commands.command(name="stats_remove")
    @commands.has_permissions(administrator=True)
    async def remove_points_libres(self, ctx, member: discord.Member, points: int):
        db = self.load_db()
        user_id = str(member.id)
        if user_id not in db or "stats" not in db[user_id]: return await ctx.send("❌ Stats introuvables.")

        actuel = db[user_id]["stats"].get("Points_Libres", 0)
        nouveau = max(0, actuel - points)
        db[user_id]["stats"]["Points_Libres"] = nouveau
        self.save_db(db)
        await ctx.send(f"⚠️ {points} points retirés à {member.mention}.")

        log_channel = self.bot.get_channel(ID_SALON_LOGS)
        if log_channel:
            embed = discord.Embed(title="⚠️ Retrait Admin", description=f"**Modo :** {ctx.author}\n**Cible :** {member}\n**Montant :** -{points}", color=discord.Color.red())
            await log_channel.send(embed=embed)

    @add_points_libres.error
    @remove_points_libres.error
    async def admin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("⛔ **Accès Refusé.** Réservé aux modos.")

# --- CETTE PARTIE ÉTAIT MANQUANTE ET CAUSAIT L'ERREUR ---
async def setup(bot):
    await bot.add_cog(Stats(bot))