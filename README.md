# FastAPI + MongoDB + Gemini Chatbot (Terminal only)

This service lets you upload a JSON file with your own articles and then chat with an AI that answers strictly based on those articles using Google Gemini.
> Note: This is a primitive chatbot built as part of the MVP for [Autonomio.app](https://autonomio.app).  
> It uses Google Gemini to answer strictly based on the uploaded articles.  


## Features
- Upload articles JSON -> stored in MongoDB (Motor, async)
- Ask questions -> build context from your stored articles -> Google Gemini
-Prompt: Answers must come ONLY from your articles; otherwise: "I don't have information on that."

## Project Structure
- `main.py` – FastAPI app and endpoints (`/upload`, `/chat`)
- `db.py` – MongoDB connection (Motor), startup/shutdown hooks
- `gemini_client.py` – Gemini API client
- `models.py` – Pydantic models for requests/responses
- `utils.py` – Helpers (context building, trimming)
- `requirements.txt` – Dependencies
- `.env.example` – Environment variable template

## Environment
Create a `.env` file (or set env vars in your shell):

```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=chatbotdb
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-1.5-flash
# TLS options (for Atlas on Windows if needed):
# MONGODB_USE_CERTIFI=true
# MONGODB_TLS_CA_BUNDLE=C:\\path\\to\\cacert.pem
# MONGODB_TLS_ALLOW_INVALID_CERTS=false
```

## Run
1. Create and activate a virtual environment (Windows PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start MongoDB (e.g., local Docker or MongoDB Community install).

3. Start the API server:

```powershell
uvicorn main:app --reload --port 8000
```

## Test with httpie
- Upload JSON file (example `articles.json`):
```powershell
http POST http://localhost:8000/upload file@articles.json
```

- Ask a question:
```powershell
http POST http://localhost:8000/chat question="What does Article 1 say?"
```

Or with curl:
```powershell
curl -X POST http://localhost:8000/upload -F "file=@articles.json"
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"question":"What does Article 1 say?"}'
```

## JSON file format
```
[
  {"title": "Article 1", "content": "This is the content of Article 1."},
  {"title": "Article 2", "content": "This is the content of Article 2."}
]
```

## Notes
- The model is instructed to answer only from the provided articles. If not answerable, it responds with: "I don't have information on that."
- Context is trimmed if too long to fit typical token limits.


