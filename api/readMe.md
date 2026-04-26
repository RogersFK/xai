pip install fastapi uvicorn sqlalchemy "passlib[bcrypt]" requests

pip install keyring

pip install python-jose --upgrade

# 1 — set your API key in app/core/config.py

ANTHROPIC_API_KEY = "sk-ant-..."

# 2 — install

pip install -r requirements.txt

# Terminal 1: server

python main.py

# Terminal 2: GUI

python client.py
