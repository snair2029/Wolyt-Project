from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)

from backend.db import Base, ENGINE, SessionLocal
from backend.models import User, Wallet, Transaction


app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me"            # move to env in real app
app.config["JWT_SECRET_KEY"] = "change-me-too"    # move to env in real app
jwt = JWTManager(app)

# create tables on startup
Base.metadata.create_all(bind=ENGINE)

# ---------- AUTH ----------
@app.post("/auth/signup")
def signup():
    data = request.get_json() or {}
    name = data.get("name")
    email = (data.get("email") or "").lower().strip()
    password = data.get("password")
    if not (name and email and password):
        return jsonify({"message": "name, email, password required"}), 400

    db = SessionLocal()
    try:
        if db.query(User).filter_by(email=email).first():
            return jsonify({"message": "email already registered"}), 409
        user = User(name=name, email=email,
                    password_hash=generate_password_hash(password))
        db.add(user); db.flush()
        # create a default wallet for the new user
        wallet = Wallet(user_id=user.id, balance=0.0)
        db.add(wallet); db.commit()
        return jsonify({"user_id": user.id, "wallet_id": wallet.id}), 201
    finally:
        db.close()

@app.post("/auth/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"message": "invalid credentials"}), 401
        token = create_access_token(identity=user.id)
        # Return default wallet id to simplify FE calls
        wallet_id = user.wallets[0].id if user.wallets else None
        return jsonify({"access_token": token, "user_id": user.id, "wallet_id": wallet_id})
    finally:
        db.close()
# ---------- WALLET / BALANCE ----------
@app.get("/balance")
@jwt_required()
def balance():
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        wallet = db.query(Wallet).filter_by(user_id=user_id).first()
        if not wallet:
            return jsonify({"message": "wallet not found"}), 404
        return jsonify({"wallet_id": wallet.id, "balance": wallet.balance})
    finally:
        db.close()

# ---------- TRANSACTION ----------
@app.post("/transaction")
@jwt_required()
def transaction():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    amount = float(data.get("amount", 0))
    receiver_wallet_id = int(data.get("receiver_wallet_id"))

    if amount <= 0:
        return jsonify({"message": "amount must be positive"}), 400

    db = SessionLocal()
    try:
        sender_wallet = db.query(Wallet).filter_by(user_id=user_id).first()
        receiver_wallet = db.query(Wallet).get(receiver_wallet_id)
        if not sender_wallet or not receiver_wallet:
            return jsonify({"message": "wallet not found"}), 404
        if sender_wallet.balance < amount:
            return jsonify({"message": "insufficient funds"}), 400

        sender_wallet.balance -= amount
        receiver_wallet.balance += amount
        tx = Transaction(sender_wallet_id=sender_wallet.id,
                         receiver_wallet_id=receiver_wallet.id,
                         amount=amount)
        db.add(tx); db.commit()
        return jsonify({"status": "success", "tx_id": tx.id})
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

# ---------- HISTORY ----------
@app.get("/history")
@jwt_required()
def history():
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        wallet = db.query(Wallet).filter_by(user_id=user_id).first()
        if not wallet:
            return jsonify({"message": "wallet not found"}), 404

        sent = db.query(Transaction).filter_by(sender_wallet_id=wallet.id).all()
        recv = db.query(Transaction).filter_by(receiver_wallet_id=wallet.id).all()
        def row(t):
            direction = "sent" if t.sender_wallet_id == wallet.id else "received"
            amount = -t.amount if direction == "sent" else t.amount
            return {"id": t.id, "amount": amount, "status": t.status, "created_at": str(t.created_at)}
        return jsonify({"transactions": [*map(row, sent), *map(row, recv)]})
    finally:
        db.close()

if __name__ == "__main__":
    import socket

    # Try to bind to 5050, else pick the next free port
    port = 5050
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            break
        except OSError:
            port += 1  # try the next port

    print(f"🚀 Starting server on http://127.0.0.1:{port}")
    app.run(debug=True, port=port)

    @app.get("/")
def home():
    return jsonify({"message": "Wolyt backend is running!"})


