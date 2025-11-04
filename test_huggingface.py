import requests
import os
from dotenv import load_dotenv
from PIL import Image
import io

# Charger les variables d'environnement
load_dotenv()

def test_huggingface():
    """Teste si l'API Hugging Face fonctionne"""
    
    # Utiliser HUGGINGFACE_TOKEN au lieu de IMAGEGEN_KEY
    HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
    
    # Vérifier si le token est chargé
    if not HUGGINGFACE_TOKEN:
        print("❌ ERREUR: La variable HUGGINGFACE_TOKEN n'est pas définie dans le fichier .env")
        print("📋 Vérifiez que votre fichier .env contient:")
        print("   HUGGINGFACE_TOKEN=hf_votre_token_ici")
        return False
    
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    
    print("🧪 Test de l'API Hugging Face...")
    print(f"🔑 Token: {HUGGINGFACE_TOKEN[:10]}...")  # Affiche seulement les 10 premiers caractères
    
    # Test simple avec un prompt basique
    prompt = "a beautiful sunset over mountains"
    
    try:
        print("📡 Envoi de la requête à Hugging Face...")
        
        response = requests.post(
            API_URL, 
            headers=headers, 
            json={"inputs": prompt},
            timeout=120  # Timeout de 2 minutes
        )
        
        print(f"📥 Statut de la réponse: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCÈS : Image générée avec succès!")
            
            # Sauvegarder l'image
            image = Image.open(io.BytesIO(response.content))
            image.save("test_huggingface_image.jpg")
            print("💾 Image sauvegardée: test_huggingface_image.jpg")
            
            # Afficher les informations de l'image
            print(f"📐 Taille de l'image: {image.size}")
            print(f"🎨 Format: {image.format}")
            
            return True
            
        elif response.status_code == 503:
            print("⏳ Le modèle est en cours de chargement...")
            print("ℹ️  Cela peut prendre 1-2 minutes lors du premier appel")
            print("🔄 Réessayez dans 1 minute")
            return "loading"
            
        else:
            print(f"❌ ERREUR: {response.status_code}")
            print(f"📄 Détails: {response.text[:500]}")  # Limite à 500 caractères
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT: La requête a pris trop de temps")
        return False
        
    except requests.exceptions.ConnectionError:
        print("🔌 ERREUR DE CONNEXION: Impossible de se connecter à l'API")
        return False
        
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TEST HUGGING FACE AVEC HUGGINGFACE_TOKEN")
    print("=" * 50)
    
    # Test principal
    result = test_huggingface()
    
    if result == "loading":
        print("\n" + "=" * 50)
        print("🔄 MODÈLE EN CHARGEMENT")
        print("=" * 50)
        print("Le modèle Stable Diffusion est en cours de chargement.")
        print("C'est normal pour la première utilisation.")
        print("Attendez 1-2 minutes puis réessayez:")
        print(">>> python test_huggingface_correct.py")
        
    elif result:
        print("\n" + "=" * 50)
        print("🎉 TOUT FONCTIONNE PARFAITEMENT!")
        print("=" * 50)
        print("Votre configuration Hugging Face est correcte.")
        print("Vous pouvez maintenant utiliser la génération d'image dans Django.")
        
    else:
        print("\n" + "=" * 50)
        print("❌ PROBLÈME DÉTECTÉ")
        print("=" * 50)
        print("Vérifiez :")
        print("1. Votre token Hugging Face dans .env")
        print("2. Votre connexion internet")
        print("3. Que le token a les permissions API")