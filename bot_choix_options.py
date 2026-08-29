import json
import os
import re
import unicodedata
from pathlib import Path

import discord
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0") or 0)

# Le nom du salon peut être écrit avec espaces ou tirets.
CHANNEL_ID = int(os.getenv("OPTIONS_CHANNEL_ID", "0") or 0)
CHANNEL_NAME = os.getenv(
    "OPTIONS_CHANNEL_NAME", "choix des options"
).strip()

STATE_FILE = BASE_DIR / ".options_reaction_state.json"
OPTIONS_FILE = BASE_DIR / "options.json"

if not TOKEN:
    raise SystemExit("❌ DISCORD_BOT_TOKEN manque dans .env")
if not GUILD_ID:
    raise SystemExit("❌ DISCORD_GUILD_ID manque dans .env")

with OPTIONS_FILE.open("r", encoding="utf-8") as f:
    OPTIONS = json.load(f)

intents = discord.Intents.default()
intents.guilds = True
intents.reactions = True

client = discord.Client(intents=intents)


def normalize_name(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(
        c for c in text if unicodedata.category(c) != "Mn"
    )
    text = re.sub(r"[\s_\-]+", "", text)
    return text.strip()


def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_option_by_emoji(emoji: str):
    for option in OPTIONS:
        if option["emoji"] == emoji:
            return option
    return None


def get_role(guild: discord.Guild, role_name: str):
    return discord.utils.get(guild.roles, name=role_name)


def find_options_channel(guild: discord.Guild):
    if CHANNEL_ID:
        channel = guild.get_channel(CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            return channel

    wanted = normalize_name(CHANNEL_NAME)

    for channel in guild.text_channels:
        if normalize_name(channel.name) == wanted:
            return channel

    # Reconnaît automatiquement les deux formes usuelles.
    accepted = {
        normalize_name("choix des options"),
        normalize_name("choix-des-options"),
    }

    for channel in guild.text_channels:
        if normalize_name(channel.name) in accepted:
            return channel

    return None


async def ensure_option_roles(guild: discord.Guild):
    """
    Crée les 15 rôles s'ils n'existent pas.
    Les rôles n'accordent aucune permission sensible :
    ils servent de rôles de choix / d'accès.
    """
    created = 0

    for option in OPTIONS:
        role_name = option["role"]
        role = get_role(guild, role_name)

        if role is None:
            try:
                role = await guild.create_role(
                    name=role_name,
                    permissions=discord.Permissions.none(),
                    hoist=False,
                    mentionable=False,
                    reason=(
                        "Création automatique du rôle "
                        f"pour l'option {option['numero']:02d}"
                    ),
                )
                created += 1
                print(f"✅ Rôle créé : {role_name}")

            except discord.Forbidden:
                raise RuntimeError(
                    "Le bot n'a pas la permission « Gérer les rôles »."
                )
        else:
            print(f"↪ Rôle déjà présent : {role_name}")

    return created


def build_choice_embed():
    embed = discord.Embed(
        title="🔮 Choix des options",
        description=(
            "Choisis les manuels optionnels que tu souhaites suivre "
            "en cliquant sur les réactions correspondantes.\n\n"
            "✨ Tu peux choisir **plusieurs options**.\n"
            "↩️ Si tu retires une réaction, le rôle correspondant "
            "te sera automatiquement retiré."
        ),
    )

    lines = []
    for option in OPTIONS:
        lines.append(
            f"{option['emoji']}  **Option {option['numero']:02d} — "
            f"{option['nom']}**"
        )

    # Réparti en deux champs pour une meilleure lisibilité.
    embed.add_field(
        name="📚 Options 01 à 08",
        value="\n".join(lines[:8]),
        inline=False,
    )
    embed.add_field(
        name="📚 Options 09 à 15",
        value="\n".join(lines[8:]),
        inline=False,
    )
    embed.add_field(
        name="🗝️ Comment ça fonctionne ?",
        value=(
            "• Ajoute une réaction → le rôle est ajouté.\n"
            "• Ajoute plusieurs réactions → plusieurs rôles sont ajoutés.\n"
            "• Retire une réaction → le rôle correspondant est retiré."
        ),
        inline=False,
    )

    embed.set_footer(
        text=(
            "Les rôles d'options peuvent ensuite être utilisés "
            "pour gérer l'accès aux salons correspondants."
        )
    )
    return embed


async def ensure_choice_message(channel: discord.TextChannel):
    """
    Réutilise le message créé précédemment si possible.
    Si les noms des options ont changé, l'embed est mis à jour.
    """
    state = load_state()
    message = None

    if (
        state.get("guild_id") == channel.guild.id
        and state.get("channel_id") == channel.id
        and state.get("message_id")
    ):
        try:
            message = await channel.fetch_message(
                int(state["message_id"])
            )
        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
            ValueError,
        ):
            message = None

    if message is None:
        message = await channel.send(embed=build_choice_embed())
        save_state({
            "guild_id": channel.guild.id,
            "channel_id": channel.id,
            "message_id": message.id,
        })
        print("✅ Message de choix créé.")
    else:
        try:
            await message.edit(embed=build_choice_embed())
            print("✅ Message de choix vérifié / mis à jour.")
        except discord.HTTPException:
            pass

    # Ajoute toutes les réactions manquantes.
    existing = {str(r.emoji) for r in message.reactions}

    for option in OPTIONS:
        if option["emoji"] not in existing:
            try:
                await message.add_reaction(option["emoji"])
            except discord.HTTPException as exc:
                print(
                    f"⚠️ Impossible d'ajouter "
                    f"{option['emoji']} : {exc}"
                )

    return message


async def handle_reaction(payload, adding: bool):
    if payload.guild_id != GUILD_ID:
        return

    if client.user and payload.user_id == client.user.id:
        return

    state = load_state()

    if payload.message_id != state.get("message_id"):
        return
    if payload.channel_id != state.get("channel_id"):
        return

    option = get_option_by_emoji(str(payload.emoji))
    if option is None:
        return

    guild = client.get_guild(payload.guild_id)
    if guild is None:
        return

    role = get_role(guild, option["role"])
    if role is None:
        print(
            f"⚠️ Le rôle n'existe plus : {option['role']}"
        )
        return

    member = payload.member

    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            return

    try:
        if adding:
            if role not in member.roles:
                await member.add_roles(
                    role,
                    reason=(
                        f"Choix de l'option "
                        f"{option['numero']:02d} par réaction"
                    ),
                )
                print(
                    f"➕ {member} → {option['role']}"
                )

        else:
            if role in member.roles:
                await member.remove_roles(
                    role,
                    reason=(
                        f"Retrait de l'option "
                        f"{option['numero']:02d} par réaction"
                    ),
                )
                print(
                    f"➖ {member} → {option['role']}"
                )

    except discord.Forbidden:
        print(
            "\n❌ Discord refuse la modification du rôle.\n"
            "Vérifie :\n"
            "1. Le bot possède « Gérer les rôles ».\n"
            "2. Dans Paramètres du serveur > Rôles, "
            "le rôle DU BOT est placé AU-DESSUS "
            "des 15 rôles d'options.\n"
        )


@client.event
async def on_raw_reaction_add(payload):
    await handle_reaction(payload, True)


@client.event
async def on_raw_reaction_remove(payload):
    await handle_reaction(payload, False)


@client.event
async def on_ready():
    print("=" * 68)
    print(f"🤖 Bot connecté : {client.user}")

    guild = client.get_guild(GUILD_ID)

    if guild is None:
        print(
            "❌ Serveur introuvable.\n"
            "Vérifie DISCORD_GUILD_ID et assure-toi que "
            "le bot a bien été ajouté à ce serveur."
        )
        print("=" * 68)
        return

    print(f"🏛️ Serveur : {guild.name}")

    channel = find_options_channel(guild)

    if channel is None:
        print(
            "❌ Salon « choix des options » introuvable.\n"
            "Solution la plus fiable : active le Mode développeur "
            "dans Discord, copie l'ID du salon et mets-le dans "
            "OPTIONS_CHANNEL_ID dans le fichier .env."
        )
        print("=" * 68)
        return

    print(f"🔮 Salon trouvé : #{channel.name}")

    try:
        created = await ensure_option_roles(guild)
        await ensure_choice_message(channel)

    except RuntimeError as exc:
        print(f"❌ {exc}")
        print("=" * 68)
        return

    except discord.Forbidden:
        print(
            "❌ Permissions insuffisantes.\n"
            "Le bot doit pouvoir : Envoyer des messages, "
            "Ajouter des réactions, Lire l'historique "
            "et Gérer les rôles."
        )
        print("=" * 68)
        return

    print(f"📚 15 options configurées.")
    print(f"🎭 Nouveaux rôles créés : {created}")
    print("✅ Système de choix par réactions actif.")
    print("=" * 68)


client.run(TOKEN, log_handler=None)
