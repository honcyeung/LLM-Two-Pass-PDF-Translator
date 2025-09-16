import fitz
import json
import os
from google.cloud import storage

SOURCE_PDF_PATH = "./pdf/El camino del libertario (Javier Milei).pdf"
EXTRACTED_DATA_PATH = "./extracted_content/data.json"
BUCKET = "my-book-translation-bucket" 

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def extract_content():

    doc = fitz.open(SOURCE_PDF_PATH)

    content_structure = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] == 0:
                block_text = "".join([span['text'] for line in block['lines'] for span in line['spans']])
                if block_text.strip():
                    content_structure.append({
                        "type": "text",
                        "page": page_num + 1,
                        "content": block_text.strip(),
                        "bbox": block["bbox"]
                    })
    
    # Sort content based on page and vertical position (y-coordinate)
    content_structure.sort(key = lambda item: (item['page'], item['bbox'][1]))
    # print(content_structure[:100])

    with open(EXTRACTED_DATA_PATH, "w", encoding = "utf-8") as f:
        json.dump(content_structure, f, indent = 4, ensure_ascii = False)

extract_content()