import random

CLASSES = ["plastique", "papier_carton", "verre", "metal",
           "textile", "autre", "tapis_vide"]

def predict(image_path):
    """FAUX MODELE : renvoie un résultat au hasard.
    Sera remplacé par le vrai modèle, sans changer la façon de l'appeler."""
    return {
        "type": random.choice(CLASSES),
        "confiance": round(random.uniform(0.2, 0.99), 2),
    }

if __name__ == "__main__":
    for _ in range(5):
        print(predict("une_image.jpg"))