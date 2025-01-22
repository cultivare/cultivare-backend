import json
from app.database import db
import shutil
import os
import glob
from datetime import datetime
from bson import ObjectId, Timestamp
from app.config import settings


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()  # Convert datetime to ISODate string
        elif isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, Timestamp):
            return o.as_datetime().isoformat()
        else:
            return super().default(o)


def copy_example_images():
    """
    Copies all .webp files from the example folder to the uploads folder.
    """

    source_folder = "app/db_example/uploads_example"
    destination_folder ="uploads"

    # Use glob to find all .webp files in the source folder
    webp_files = glob.glob(os.path.join(source_folder, "*.webp"))

    # Iterate through the list of .webp files
    for file_path in webp_files:
        # Extract the filename from the file path
        filename = os.path.basename(file_path)

        # Construct the destination path for the file
        destination_path = os.path.join(destination_folder, filename)

        # Copy the file using shutil.copy2
        shutil.copy2(file_path, destination_path)
        print(f"Copied {filename} to {destination_folder}")


async def export_collection_data():
    """Exports the entire collection data to a JSON file."""
    collection_names = ["cultures", "notes"]
    for collection_name in collection_names:
        collection = db.db[collection_name]
        cursor = collection.find({})  # Find all documents
        data = await cursor.to_list(length=None)  # Fetch all documents

        # Remove the _id field (if not needed)
        for document in data:
            if "_id" in document:
                del document["_id"]

        with open(f"app/db_example/{collection_name}.json", "w") as f:
            json.dump(data, f, indent=4, cls=CustomJSONEncoder)


# Import function
async def import_collection_data():
    collection_names = ["cultures", "notes"]
    for collection_name in collection_names:
        collection = db.db[collection_name]
        filename = f"app/db_example/{collection_name}.json"
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            if data:
                await collection.drop()
                await collection.insert_many(data)
                print(f"Data imported successfully into {collection_name}")
            else:
                print(f"No data found in {filename}")
        except FileNotFoundError:
            print(f"File {filename} not found.")


# Init DB function
async def init_db():
    if not settings.INIT_EXAMPLE_DB:
        print("Skipping initialization.")
        return False

    collection = db.db["cultures"]
    count = await collection.count_documents({})
    if count == 0:
        print("Database is empty. Initializing with example data...")
        copy_example_images()
        await import_collection_data()
    else:
        print("Database already contains data. Skipping initialization.")


# asyncio.run(init_db()) # init
# asyncio.run(export_collection_data()) # export
