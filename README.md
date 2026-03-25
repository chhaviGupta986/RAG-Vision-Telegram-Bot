# Telegram RAG + Vision Bot

Telegram bot that:

- answers questions from your own document set (RAG), and
- captions images, then generates short tags.

## System Flow
<img width="1106" height="498" alt="image" src="https://github.com/user-attachments/assets/ac7cb0ee-a4a2-43fa-9bdb-27a7d8153efa" />

## Demo
https://github.com/user-attachments/assets/e7a4d33e-eea9-4ccb-ad3b-87520d51a177

## What This Project Covers

- End-to-end RAG flow with local vector search
- Telegram bot command handling
- Image captioning + LLM-assisted tagging
- Maintains conversation history of upto past 3 chats
- Does query caching

## Models and APIs Used

- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- LLM (Ollama): `phi3:mini`
- Image captioning model (Hugging Face): `Salesforce/blip-image-captioning-base`
- Telegram API: via `python-telegram-bot`
- Ollama API endpoint: `http://127.0.0.1:11434/api/chat`

## Tech Stack

- Python 3.10+
- `python-telegram-bot`
- `sentence-transformers`
- `faiss-cpu`
- `langchain`, `langchain-text-splitters`
- `transformers`, `torch`, `torchvision`, `Pillow`
- `requests`, `python-dotenv`

## How to Run Locally

1. Create environment

```bash
# venv (macOS/Linux)
python -m venv .venv
source .venv/bin/activate

# venv (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# conda (alternative)
conda create -n telegram-bot python=3.10 -y
conda activate telegram-bot
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure environment variables (in `.env`)

```env
TELEGRAM_TOKEN=your_bot_token
HUGGINGFACE_TOKEN=your_hf_token
```

4. Add source docs to `data/`, then build index

```bash
python build_index.py
```

5. Start Ollama and pull required models

```bash
ollama serve
ollama pull phi3:mini (Run in another terminal, if not already executed. It is a one time operation to pull the model onto local machine)
```

6. Run bot

```bash
python app.py
```

## Bot Commands

- `/ask <question>`: answer from indexed docs
- `/image`: next uploaded image is captioned + tagged
- `/summarize`: summarizes only the latest bot response
- `/help`: shows command list

## Caching Behavior

- Max size of cache is 100 entries; older responses are dropped once the limit is reached.
- The cache only activates when there is no conversation history attached to the question (i.e., the first turn). Once the last 3 exchanges are passed into the prompt, the cached entry is skipped so the LLM always sees the updated context and you never return stale material.
- Cache is persisted to `db/query_cache.pkl` and reloaded at startup, so restarts can still hit cached answers.
- Deleting the cache file makes the next run start from scratch again.
- The cache also persists to `db/query_cache.pkl`, so answers can survive restarts and still shortcut repeated cold-start queries.

## Troubleshooting

- **High Latency/Timeouts**: If Ollama calls time out (for example: `ReadTimeout ... 127.0.0.1:11434`), the model is often too heavy for your laptop, especially on CPU-only setups.
In that case, switch to a smaller model such as `smollm:135m` instead of `phi3`.
- Pull and use some smaller model:
```bash
ollama pull smollm:135m
```
and change the model name in rag.py and vision.py accordingly.

- **Ollama unreachable**: Verify `ollama serve` is running and `curl http://127.0.0.1:11434/api/models` works before pinging the bot.
- **No relevant context**: After adding docs rerun `python build_index.py`. Inspect `db/chunks_debug.txt` for the generated chunks; if they are too long , adjust the chunk size/overlap.
