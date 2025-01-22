import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    MONGODB_URL = os.getenv("CULTIVARE_MONGODB_URL")
    DATABASE_NAME = os.getenv("CULTIVARE_DATABASE_NAME")
    CULTURES_COLLECTION_NAME = "cultures" or os.getenv("CULTIVARE_CULTURES_COLLECTION_NAME")
    NOTES_COLLECTION_NAME = "notes" or os.getenv("CULTIVARE_NOTES_COLLECTION_NAME")

    FRONTEND_URL = os.getenv("CULTIVARE_FRONTEND_URL")
    MEDIA_DIR = "uploads" or os.getenv("CULTIVARE_MEDIA_DIR")
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"} # for note's attachment

    # Printer settings:
    PRINTER_BACKEND = os.getenv("CULTIVARE_PRINTER_BACKEND")
    PRINTER_MODEL = os.getenv("CULTIVARE_PRINTER_MODEL")
    PRINTER_ADDRESS = os.getenv("CULTIVARE_PRINTER_ADDRESS") # ip address like tcp://192.168.0.10 or usb values from the Windows usb driver filter.  Linux/Raspberry Pi uses '/dev/usb/lp0'.
    PRINTER_LABEL_SIZE = os.getenv("CULTIVARE_PRINTER_LABEL_SIZE")

settings = Settings()
