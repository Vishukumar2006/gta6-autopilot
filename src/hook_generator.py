"""Viral Hook & SEO Generator for GTA 6 Shorts & Reels."""

import random
from typing import Dict, List, Any


class HookGenerator:
    """Generates viral hooks, titles, captions, and tags tailored for GTA 6."""

    HOOK_TEMPLATES = {
        "leak": [
            "ROCKSTAR LEAKED THIS IN GTA 6! 🚨",
            "THEY DIDN'T WANT YOU TO SEE THIS 😱",
            "SECRET GTA 6 FEATURE DISCOVERED! 👀",
            "CONFIRMED IN GTA 6 VICE CITY! 🔥",
            "LOOK AT THIS HIDDEN DETAIL IN GTA 6! 🕵️",
        ],
        "action": [
            "THE POLICE AI IN GTA 6 IS INSANE! 🚔",
            "HE TRIED TO ESCAPE 5 STARS IN GTA 6 💀",
            "BEST CAR CHASE IN GTA 6 SO FAR! 🏎️💨",
            "THIS WEAPON IN GTA 6 IS OVERPOWERED! 💥",
            "HE CANNOT BELIEVE WHAT JUST HAPPENED! 🤯",
        ],
        "physics": [
            "THIS IS WHY GTA 6 TOOK 12 YEARS! 🌊",
            "GTA 6 WATER PHYSICS LOOK TOO REAL! 🤯",
            "LOOK AT THE NPC REACTIONS IN GTA 6! 🧍",
            "NEXT-GEN GRAPHICS IN VICE CITY 🌴✨",
            "REAL LIFE OR GTA 6? YOU DECIDE! 🎮",
        ],
        "funny": [
            "WAIT FOR THE END... HE LOST IT! 😭💀",
            "STREAMER REGRETTED THIS IMMEDIATELY! 🤣",
            "ONLY IN GTA 6 VICE CITY! 🌴😂",
            "HE THOUGHT HE WAS SAFE... 💀",
            "TOP 1% MOMENT IN GTA 6! 🏆",
        ],
    }

    GENERIC_VIRAL_HOOKS = [
        "WAIT TILL THE END... 😱",
        "NO WAY THIS IS REAL! 🚨",
        "YOU WON'T BELIEVE THIS IN GTA 6! 🔥",
        "DID YOU SPOT THIS SECRET? 👀",
        "THIS CHANGES EVERYTHING FOR GTA 6! 🤯",
    ]

    TAG_POOL = [
        "#gta6",
        "#gtavi",
        "#gta6gameplay",
        "#gta6leaks",
        "#rockstargames",
        "#vicecity",
        "#grandtheftauto",
        "#gaming",
        "#gamers",
        "#gamingcommunity",
        "#shorts",
        "#reels",
        "#viral",
        "#fyp",
        "#explorepage",
    ]

    CTA_TEMPLATES = [
        "Follow @GTA6Pulse for daily leaks & crazy moments! 🔥",
        "Subscribe & drop a like if you are hyped for GTA 6! 🎮",
        "Drop a comment: Will you buy GTA 6 Day 1? 💬",
        "Share this with a friend who is waiting for GTA 6! 🚀",
    ]

    @classmethod
    def generate_hook(
        cls, category: str = "action", keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Generate a complete package of hook, title, description, and hashtags."""
        hooks = cls.HOOK_TEMPLATES.get(category, cls.GENERIC_VIRAL_HOOKS)
        chosen_hook = random.choice(hooks)

        # Title: punchy, under 65 chars
        title = f"{chosen_hook} #GTA6 #Shorts"
        if len(title) > 90:
            title = chosen_hook

        # Hashtags: Ensure core primary tags #gta6 and #gtavi are always present
        core_tags = ["#gta6", "#gtavi"]
        pool_remaining = [t for t in cls.TAG_POOL if t not in core_tags]
        selected_tags = core_tags + random.sample(pool_remaining, k=min(6, len(pool_remaining)))
        hashtags_str = " ".join(selected_tags)

        # CTA
        cta = random.choice(cls.CTA_TEMPLATES)

        # Description
        description = (
            f"{chosen_hook}\n\n"
            f"Crazy moment captured in Grand Theft Auto VI (GTA 6)!\n\n"
            f"{cta}\n\n"
            f"{hashtags_str}"
        )

        return {
            "hook_text": chosen_hook,
            "title": title,
            "description": description,
            "caption": f"{chosen_hook} 🌴\n{cta}\n\n{hashtags_str}",
            "hashtags": hashtags_str,
            "category": category,
        }

    @classmethod
    def detect_category_from_text(cls, text: str) -> str:
        """Categorize stream or segment by title keywords."""
        lower = text.lower()
        if any(w in lower for w in ["leak", "secret", "rumor", "hidden", "trailer", "rockstar"]):
            return "leak"
        elif any(w in lower for w in ["physics", "graphic", "unreal", "real", "water", "npc"]):
            return "physics"
        elif any(w in lower for w in ["funny", "fail", "rage", "streamer", "reaction", "lol"]):
            return "funny"
        else:
            return "action"
