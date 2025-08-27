import fitz
import json
import os
from google.cloud import storage

SOURCE_PDF_PATH = "./pdf/El camino del libertario (Javier Milei).pdf"
EXTRACTED_DATA_PATH = "./extracted_content/data.json"
IMAGE_DIR = "./extracted_content/images"
BUCKET_NAME = "my-book-translation-bucket" # Optional: for cloud backup

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def extract_content():

    doc = fitz.open(SOURCE_PDF_PATH)
    # os.makedirs(IMAGE_DIR, exist_ok = True)

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
    
    # Extract images
        # image_list = page.get_images(full=True)
        # for img_index, img in enumerate(image_list):
        #     xref = img[0]
        #     base_image = doc.extract_image(xref)
        #     image_bytes = base_image["image"]
        #     image_ext = base_image["ext"]
        #     image_filename = f"page_{page_num + 1}_img_{img_index}.{image_ext}"
        #     image_path = os.path.join(IMAGE_DIR, image_filename)
            
        #     with open(image_path, "wb") as img_file:
        #         img_file.write(image_bytes)
            
        #     content_structure.append({
        #         "type": "image",
        #         "page": page_num + 1,
        #         "path": image_path,
        #         "bbox": page.get_image_bbox(img).irect # Bounding box
        #     })
            # Optional: upload image to GCS
            # upload_to_gcs(BUCKET_NAME, image_path, f"images/{image_filename}")
    
    # Sort content based on page and vertical position (y-coordinate)
    content_structure.sort(key = lambda item: (item['page'], item['bbox'][1]))
    # print(content_structure[:100])

    with open(EXTRACTED_DATA_PATH, "w", encoding = "utf-8") as f:
        json.dump(content_structure, f, indent = 4, ensure_ascii = False)

extract_content()