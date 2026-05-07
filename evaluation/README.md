This folder contains the code used to carry out automatic evaluations of the tested RAG pipeline configurations.

## Workflow Overview

The evaluation process follows a two-stage pipeline:

1. **Answer Generation** (`generate_answers.py`): Takes a CSV file with test questions and feeds them through the RAG system, storing the generated answers and retrieved context in a new CSV.
2. **Evaluation** (`evaluation.py`): Takes the CSV produced by step 1 and computes automatic metrics using Ragas and VertexAI models. Outputs metrics and aggregated statistics in a results CSV. Requires access to a Google Cloud project with Vertex AI enabled and valid Google Cloud credentials.

## Note

Aside from the dependencies declared in the `requirements.txt` file in the repository's root, the scripts in this folder require the dependencies in the `requirements.txt` in this folder to work.