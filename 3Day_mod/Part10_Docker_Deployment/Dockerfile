# Single image for the whole Banking KB RAG Assistant. The ingestion
# pipeline (Parts 2-5), the FastAPI backend (Part 8), and the Streamlit
# frontend (Part 9) all run from this one image -- docker-compose.yml
# selects which by overriding the command per service, so there's exactly
# one set of dependencies to build and one image to keep in sync.
#
# Build context is the project root (3Day_mod/), not this folder -- see
# docker-compose.yml's `context: ..`.
FROM python:3.13-slim

WORKDIR /app

# faiss-cpu and psycopg2-binary both ship manylinux wheels for this base
# image, so no compiler/build-essential is needed here.
COPY Part1_Environment_Setup/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8501
