from google.cloud import firestore
from dotenv import load_dotenv
import json
import os
import warnings

warnings.filterwarnings('ignore')

TRANSLATED_DATA_PATH = "./translated_content/translated_data.json"

load_dotenv()
PROJECT_ID = os.environ["PROJECT_ID"]
COLLECTION_NAME = os.environ["COLLECTION_NAME"]

def create_document_id(block):

    # We zero-pad the page number and the 'top' coordinate from the bbox.
    # This guarantees that Firestore's alphabetical sorting will match the
    # book's natural reading order.
    page_num = str(block.get("page", 0)).zfill(5)
    top_coord = str(int(block.get("bbox", [0, 0, 0, 0])[1])).zfill(5)
    doc_id = f"page_{page_num}_top_{top_coord}"

    return doc_id

def store_translated_blocks_to_firestore(block_id, data_block):

    try:
        db = firestore.Client(PROJECT_ID)
        doc_ref = db.collection(COLLECTION_NAME).document(block_id)
        if doc_ref.get().exists:
            print(f"Document with ID: {block_id} already exists. Skipping write.")
            return
        doc_ref.set(data_block)
    except Exception as e:
        print(f"Error storing document {block_id}: {e}")
        return

try:
    with open(TRANSLATED_DATA_PATH, "r", encoding = "utf-8") as f:
        translated_blocks = json.load(f)
except Exception as e:
    print(f"Error: {e}")

for block in translated_blocks:
    doc_id = create_document_id(block)
    store_translated_blocks_to_firestore(doc_id, block)