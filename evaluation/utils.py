import os
import base64
import requests
from datetime import datetime
from django.conf import settings
from .models import Badge

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

def generer_badge_image(type_badge):
    if not STABILITY_API_KEY:
        print("❌ API KEY Stability manquante")
        return None

    prompt = f"A shiny {type_badge.lower()} medal badge, high quality, 3D render, HD resolution"

    url = "https://api.stability.ai/v2beta/stable-image/generate/core"

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "image/*",   # ✅ correct
    }

    files = {
        "prompt": (None, prompt),
        "output_format": (None, "png"),
    }

    # ✅ Multipart form-data obligatoire !
    response = requests.post(url, headers=headers, files=files)

    if response.status_code != 200:
        print("❌ Erreur API Stability :", response.text)
        return None

    img_bytes = response.content  # ✅ données image directement

    filename = f"badge_{type_badge.lower()}_{int(datetime.now().timestamp())}.png"
    folder = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)

    with open(path, "wb") as f:
        f.write(img_bytes)

    print("✅ Badge généré :", filename)
    return f"badges/{filename}"



def creer_achievement_automatique(examen):
    if examen.note_max >= 18:
        type_badge = "GOLD"
    elif examen.note_max >= 12:
        type_badge = "SILVER"
    else:
        type_badge = "BRONZE"

    badge, created = Badge.objects.get_or_create(type=type_badge)

    if created or not badge.image:
        img_path = generer_badge_image(type_badge)
        if img_path:
            badge.image = img_path
            badge.save()

    examen.badge = badge
    examen.save()
