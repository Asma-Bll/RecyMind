import os

# Une seule base de test pour tous les fichiers de test (SQLite, aucun PostgreSQL necessaire)
os.environ.setdefault("SECRET_KEY", "cle_de_test")
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
