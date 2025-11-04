import os
import replicate
from dotenv import load_dotenv

load_dotenv()

# Testez directement Replicate
def test_replicate():
    try:
        print("🧪 Test de Replicate...")
        
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": "Professional event banner for a Hackathon, modern design, vibrant colors",
                "width": 512,
                "height": 512,
            }
        )
        
        print("✅ Replicate fonctionne!")
        print(f"URL de l'image: {output[0]}")
        return True
    except Exception as e:
        print(f"❌ Erreur Replicate: {e}")
        return False

if __name__ == "__main__":
    test_replicate()