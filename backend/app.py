from flask import Flask, jsonify, request, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from flask_cors import CORS
from sqlalchemy import text

from ml.trust_score import compute_trust_score

from backend.db import Base, ENGINE, SessionLocal
from backend.models import User, Wallet, Transaction

# Serve ../frontend as static so "/" loads index.html
app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

app.config["SECRET_KEY"] = "change-me"             # move to env in real app
app.config["JWT_SECRET_KEY"] = "change-me-too"     # move to env in real app
jwt = JWTManager(app)

# create tables on startup
Base.metadata.create_all(bind=ENGINE)

# ---------- STATIC HOME ----------
@app.get("/")
def home_page():
    return send_from_directory(app.static_folder, "index.html")

# ---------- AUTH ----------
@app.post("/auth/signup")
def signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").lower().strip()
    password = (data.get("password") or "").strip()
    if not (name and email and password):
        return jsonify({"message": "name, email, password required"}), 400

    db = SessionLocal()
    try:
        if db.query(User).filter_by(email=email).first():
            return jsonify({"message": "email already registered"}), 409

        user = User(name=name, email=email,
                    password_hash=generate_password_hash(password))
        db.add(user); db.flush()

        wallet = Wallet(user_id=user.id, balance=0.0)
        db.add(wallet); db.commit()
        return jsonify({"user_id": user.id, "wallet_id": wallet.id}), 201
    finally:
        db.close()

@app.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").lower().strip()
    password = (data.get("password") or "").strip()

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"message": "invalid credentials"}), 401
        token = create_access_token(identity=user.id)
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
        return jsonify({"wallet_id": wallet.id, "balance": float(wallet.balance)})
    finally:
        db.close()

# ---------- TRANSACTION ----------
@app.post("/transaction")
@jwt_required()
def transaction():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0))
        receiver_wallet_id = int(data.get("receiver_wallet_id"))
    except (TypeError, ValueError):
        return jsonify({"message": "invalid amount or receiver_wallet_id"}), 400
    if amount <= 0:
        return jsonify({"message": "amount must be positive"}), 400

    db = SessionLocal()
    try:
        sender_wallet = db.query(Wallet).filter_by(user_id=user_id).first()
        receiver_wallet = db.get(Wallet, receiver_wallet_id)
        if not sender_wallet or not receiver_wallet:
            return jsonify({"message": "wallet not found"}), 404
        if float(sender_wallet.balance) < amount:
            return jsonify({"message": "insufficient funds"}), 400

        sender_wallet.balance = float(sender_wallet.balance) - amount
        receiver_wallet.balance = float(receiver_wallet.balance) + amount

        tx = Transaction(
            sender_wallet_id=sender_wallet.id,
            receiver_wallet_id=receiver_wallet.id,
            amount=amount,
            status="completed"
        )
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

        def row(t: Transaction):
            direction = "sent" if t.sender_wallet_id == wallet.id else "received"
            amount = -float(t.amount) if direction == "sent" else float(t.amount)
            ts = (t.created_at.isoformat(timespec="seconds")
                  if hasattr(t.created_at, "isoformat") else str(t.created_at))
            return {
                "id": t.id,
                "direction": direction,
                "amount": amount,
                "status": t.status,
                "created_at": ts,
            }

        # newest first
        items = [*map(row, sent), *map(row, recv)]
        items.sort(key=lambda x: x["created_at"], reverse=True)
        return jsonify({"transactions": items})
    finally:
        db.close()

# ---------- DEV RESET (local only) ----------
@app.post("/dev/reset")
def dev_reset():
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM transactions"))
        db.execute(text("DELETE FROM wallets"))
        db.execute(text("DELETE FROM users"))
        db.commit()
        return jsonify({"reset": "ok"}), 200
    finally:
        db.close()

# ---------- TRUST SCORE ----------
@app.get("/trust-score/<int:user_id>")
def trust_score(user_id: int):
    db = SessionLocal()
    try:
        from backend import models
        user = db.get(User, user_id)
        if not user:
            return jsonify({"message": "user not found"}), 404
        result = compute_trust_score(user_id, db, models)
        return jsonify(result), 200
    finally:
        db.close()

# ---------- UTIL ----------
@app.get("/whoami")
@jwt_required()
def whoami():
    return jsonify({"user_id": get_jwt_identity()})

@app.get("/ping")
def ping():
    return jsonify({"ok": True})

@app.get("/health")
def health_check():
    db = SessionLocal()
    try:
        users_count = db.query(User).count()
        return jsonify({"status": "ok", "users_in_db": users_count}), 200
    finally:
        db.close()

# ---------- APP START ----------
if __name__ == "__main__":
    import socket
    host = "127.0.0.1"
    port = 5050
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            sock.bind((host, port)); sock.close(); break
        except OSError:
            port += 1
    print(f"🚀 Starting server on http://{host}:{port}")
    app.run(debug=True, host=host, port=port)
