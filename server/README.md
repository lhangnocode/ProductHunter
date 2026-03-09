# Server

### Manual run the server
```bash
#(assuming you are in the root directory of the project)
cd server 
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```