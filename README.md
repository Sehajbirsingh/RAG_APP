# Retail RAG App

React + FastAPI version of the notebook prototype.

## Backend

```bash
cd Retail_RAG
.venv/bin/pip install -r RAG_APP/backend/requirements.txt
.venv/bin/uvicorn app:app --app-dir RAG_APP/backend --host 0.0.0.0 --port 8000
```

The backend uses `/Users/temp/Documents/Retail_RAG/product_embeddings_final.pkl` by default.

## Frontend

```bash
cd RAG_APP/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.
