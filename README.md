# Bot Discord — Choix des 15 options

Cette version contient directement les 15 intitulés officiels du catalogue.

## Les rôles créés automatiquement

Le bot crée :

1. 🪞 Catoptromancie
2. 🔮 Cristallomancie & scrying
3. 🟤 Géomancie traditionnelle
4. 🎲 Astragalomancie
5. 🌌 Magie astrale médiévale
6. 🧿 Magie talismanique & magie des images
7. 📜 Magie gréco-égyptienne - Papyri Graecae Magicae
8. ⛓️ Defixiones & sorts de ligature
9. 🛡️ Magie apotropaïque - Protection contre le mal
10. 📖 Magie rituelle des grimoires
11. 💀 Nécromancie historique & communication avec les morts
12. 🪄 Seiðr & pratiques magiques nordiques
13. 🧹 Sorcellerie populaire française & désenvoûtement
14. 🏺 Magie mésopotamienne & exorcismes de l'āšipu
15. 🩸 Le sang dans l'histoire de la magie et du rituel

Aucun de ces rôles n'obtient de permission d'administration.

## Salon utilisé

Le bot utilise le salon existant :

`choix des options`

ou :

`choix-des-options`

Pour être certain qu'il sélectionne exactement le bon salon, utilise son ID.

Dans Discord :

1. Paramètres utilisateur → Avancé → Mode développeur
2. clic droit sur le salon
3. Copier l'identifiant
4. colle-le dans `.env` :

```env
OPTIONS_CHANNEL_ID=123456789012345678
```

## Configuration

Copie `.env.example` et renomme la copie :

`.env`

Puis remplis :

```env
DISCORD_BOT_TOKEN=TON_TOKEN_PRIVE
DISCORD_GUILD_ID=ID_DU_SERVEUR
OPTIONS_CHANNEL_NAME=choix des options
OPTIONS_CHANNEL_ID=0
```

Ne partage jamais ton token.

## Permissions nécessaires

Le bot doit avoir :

- Voir le salon
- Envoyer des messages
- Ajouter des réactions
- Lire l'historique des messages
- Intégrer des liens
- Gérer les rôles

## TRÈS IMPORTANT : ordre des rôles

Discord interdit à un bot d'attribuer un rôle situé au-dessus de son propre rôle.

Après le premier démarrage :

1. Paramètres du serveur
2. Rôles
3. place le rôle du bot au-dessus des 15 rôles d'options

Normalement, les rôles créés par le bot sont déjà placés sous son rôle, mais vérifie si une réaction ne fonctionne pas.

## Installation Windows

Double-clique :

`1_INSTALLER.bat`

Puis :

`2_DEMARRER.bat`

Le bot créera automatiquement les rôles manquants puis publiera le message dans le salon.

Il peut être relancé : il ne recrée pas un rôle portant déjà exactement le même nom.

## Réactions

Ajouter une réaction = ajouter le rôle.

Retirer la réaction = retirer le rôle.

Un membre peut sélectionner autant d'options qu'il souhaite.

## Pas de Message Content Intent requis

Ce bot ne lit pas le contenu des messages des membres.

Il n'a donc pas besoin de **Message Content Intent**.
