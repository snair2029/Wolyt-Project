# 🚀 Wolyt Test Dashboard

This project is the **backend + frontend test dashboard** for Wolyt.  
It demonstrates API endpoints for authentication, wallets, transactions, history, and trust score, along with a simple frontend for testing.

---

## 📂 Project Structure
Wolyt-Project/
├── backend/
│ ├── app.py # Flask app (APIs, Auth, Routes)
│ ├── db.py # Database setup (SQLite + SQLAlchemy)
│ ├── models.py # ORM models (User, Wallet, Transaction)
│ └── wolytd.db # Local SQLite database
├── ml/
│ └── trust_score.py # Trust score calculation logic
├── frontend/
│ └── index.html # Test dashboard (HTML + Fetch API)
└── docs/
└── Wolyt-APIs.postman_collection.json # Postman collection (exported)

---

## ⚙️ Setup & Run

1. **Clone the repo**  
   ```bash
   git clone <repo-url>
   cd Wolyt-Project
Create a virtual environment & install dependencies

bash
Copy code
python3 -m venv .venv
source .venv/bin/activate
pip install flask flask-cors flask-jwt-extended werkzeug sqlalchemy
Run the backend

bash
Copy code
python3 -m backend.app
Server starts at:
👉 http://127.0.0.1:5050

Open the frontend

Open frontend/index.html in your browser.

Use the dashboard to call APIs (Signup, Login, Trust Score, Balance, History, Transactions).