import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()
K =os.getenv("K")
print(K)
print(type(K))
