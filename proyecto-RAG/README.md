# 1. Create virtual environment
Install pipenv:
```
pip install pipenv
```
Clone the repository:
```
git clone https://github.com/CFAA-EHU/RAG4MachiningDocs.git
```
Go to the proyecto-RAG directory inside the cloned repository.

Create virtual environment and install dependencies:
```
pipenv install
```
Activate virtual environment:
```
pipenv shell
```

# 2. Environment variables
- MISTRAL_API_KEY: MistralAI api key to be able to send requests to their API.
- HF_TOKEN: HuggingFace token.
- LANGSMITH_ENDPOINT: Langsmith endpoint depending on your region (US/Europe).
- LANGSMITH_TRACING: Enable langsmith tracing for your project (set to true).
- LANGSMITH_API_KEY: Langsmith api key to be able to use their API.

# 3. Run the project
## 3.1. Extract text from the PDF files, generate the embeddings and put them in the vector store
The load_db.py file does exactly that.
- It uses the function defined in extract_text.py to create chunks of the text in the PDF.
- It uses the function defined in extract_images.py to load the descriptions of images from the .txt file that is created by the project in the 'Image descriptions PDFs' folder in this same repository. Refer to its README to learn how it works.
- As each PDF file has its particular characteristics, we need to define a slightly different configuration for each PDF we want to process. The definitions are written in config.py. The ones in that file are the configurations used for our use case. You can use them as an example to create your own. The parameters to be defined are: document name, pages that are written in two column format, pages we don't want to process, pages that don't contain tables (sometimes the program reads as a table something that is not a table and we have to tell it that it's not so that it reads it as normal text), font size threshold to consider a phrase a title (any text with a font size bigger than the threshold is considered a title), the minimum number of characters a word must have to be considered a word (only applicable to words surpassing the font size threshold, as there was some noise in the text that was being picked up as a title but were only letters in a diagram), margin rules (the margin limits of the page, so as not to read the noise in the margins)

Define the variables in load_db.py:
- pdf_path: Path to the PDF you want to create embeddings from.
- imgs_txt_path: If you generated image descriptions for the images in that PDF with the method explained in 'Image descriptions PDFs' put the path to the .txt; if not, an empty string.
- txt_path: The path to a .txt to save the generated chunks so that you can review them and see how they were formed, to adjust the configuration accordingly.
- config: Define the config you want to use in the functions 'procesar_pdf()' and 'procesar_descripciones_imagenes()'.
- persist_directory: The path to the vectorstore to store the embeddings.

```
python load_db.py
```

Outputs:
- .txt file with the chunks to review.
- some chunks will be printed in the terminal to verify that they were correctly added to the vectorstore.

## 3.2. Run RAG pipeline
Define the variables in main.py:
- persist_directory: The path to the vectorstore to store the embeddings.
- prompt and rewrite_prompt: Define the system messages.

```
python main.py
```

## 3.3. Run evaluations
Use create_dataset_langsmith.py to create a personalized dataset in langsmith from a set of question in a CSV.
```
python create_dataset_langsmith.py
```

Use langsmith_eval.py to execute an experiment in langsmith for your dataset.
```
python langsmith_eval.py
```