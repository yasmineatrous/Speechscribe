import os
import logging
from app import app
from dotenv import load_dotenv


load_dotenv()  

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Make sure uploads directory exists
uploads_dir = os.path.join(os.getcwd(), 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
