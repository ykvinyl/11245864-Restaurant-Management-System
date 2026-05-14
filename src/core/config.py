import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "060106")
DB_NAME = os.getenv("DB_NAME", "RestaurantDB")

SECRET_KEY = os.getenv("SECRET_KEY", "f7d232a881fc1e84e847c8855fed7be1c9262c43a2710a11173c46fa0c1cb909")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))