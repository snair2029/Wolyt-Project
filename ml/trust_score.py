# ml/trust_score.py

def compute_trust_score(user_id, db, models):
    User, Wallet, Transaction = models.User, models.Wallet, models.Transaction

    # Get user and wallet
    user = db.query(User).get(user_id)
    if not user or not user.wallets:
        return {"user_id": user_id, "score": 0, "signals": {}}

    wallet = user.wallets[0]

    # Transactions sent and received
    sent = db.query(Transaction).filter_by(sender_wallet_id=wallet.id).all()
    received = db.query(Transaction).filter_by(receiver_wallet_id=wallet.id).all()

    # Trust score formula starting from 0
    score = (len(received) * 10) - (len(sent) * 5)

    # Clamp between 0 and 100
    score = max(0, min(100, score))

    return {
        "user_id": user_id,
        "score": score,
        "signals": {
            "n_sent": len(sent),
            "n_received": len(received),
            "total_in": sum(t.amount for t in received),
            "total_out": sum(t.amount for t in sent),
        },
    }
