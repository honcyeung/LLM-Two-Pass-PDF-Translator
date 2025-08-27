# **LLM Two-Pass PDF Translator**

A fully automated, two-pass translation pipeline for PDF documents. This project extracts text blocks from a PDF, uses the Google Gemini API to intelligently build a glossary of key terms, and then performs a final, consistent translation which is uploaded to Google Firestore.

## **Features**

* **PDF Text Extraction**: Parses a source PDF and extracts all text blocks, preserving metadata like page number and position.  
* **Automated Glossary Creation**: In the first pass, the script calls the Gemini API to identify and translate important recurring terms, creating a project-specific glossary.  
* **Consistent Final Translation**: In the second pass, the script uses the generated glossary to ensure that key terms are translated consistently throughout the entire document.  
* **Firestore Integration**: Uploads the final translated content, along with all original metadata, to a Google Firestore collection for easy access and use in web applications.  
* **Configurable & Automated**: The entire process is designed to be run from the command line with minimal configuration.

## **The Two-Pass Workflow**

This project uses an advanced translation technique to ensure high consistency across large documents.

1. **Phase** 1: Discovery Pass  
   * The script iterates through the source text block by block.  
   * For each block, it asks the Gemini API to identify potential key terms (proper nouns, specific concepts, etc.) and suggest translations.  
   * These approved terms are automatically compiled into a central `glossary.json` file. This glossary grows and becomes more intelligent as more of the book is processed.  
2. **Phase 2: Finalization Pass**  
   * The script starts again from the beginning of the book.  
   * For each block, it sends the original text along with the **entire completed glossary** to the Gemini API.  
   * This forces the AI to use the pre-approved translations for all key terms, resulting in a perfectly consistent final text.

## **Usage**

The pipeline is run by executing the scripts in order.

1. Extract Content from PDF:  
   This script reads the PDF, extracts all text blocks, and saves them to `extracted\_content/data.json`.  
   `python3 extract.py`

2. Run the Translation Pipeline:  
   This script performs both Phase 1 (glossary creation) and Phase 2 (final translation). It reads from `extracted\_content/data.json` and produces the glossary and the final translated file.  
   `python3 translate.py`

3. Load Data to Firestore:  
   This script takes the final `translated\_data.json` and uploads each block as a document to your specified Firestore collection.  
   `python3 load.py`

## **Project Structure**

`
.  
├── .gitignore  
├── extract.py              \# Extracts text from the source PDF  
├── translate.py            \# Main script for the two-pass translation  
├── load.py                 \# Loads the final data into Firestore  
`