# ml/trust_score.py
from math import exp

def compute_trust_score(user_id: int, db, models) -> dict:
    """
    Dummy, explainable trust score on [0, 100].
    Signals:
      - # successful transactions (sent + received)
      - total volume moved
    """
    User, Wallet, Transaction = models.User, models.Wallet, models.Transaction

    user = db.query(User).get(user_id)
    if not user:
        return {"user_id": user_id, "score": 0, "signals": {"reason": "user_not_found"}}

    wallet = db.query(Wallet).filter_by(user_id=user_id).first()
    if not wallet:
        return {"user_id": user_id, "score": 0, "signals": {"reason": "wallet_not_found"}}

    sent = db.query(Transaction).filter_by(sender_wallet_id=wallet.id).all()
    received = db.query(Transaction).filter_by(receiver_wallet_id=wallet.id).all()

    n_sent     = len(sent)
    n_received = len(received)
    total_out  = sum(t.amount for t in sent)
    total_in   = sum(t.amount for t in received)

    activity = 25 * (1 - exp(-0.1 * (n_sent + n_received)))       # 0..25
    volume   = 15 * (1 - exp(-0.001 * (total_in + total_out)))    # 0..15

    score = 50 + activity + volume
    score = max(0, min(100, round(score, 1)))

    return {
        "user_id": user_id,
        "score": score,
        "signals": {
            "n_sent": n_sent,
            "n_received": n_received,
            "total_in": total_in,
            "total_out": total_out,
        },
    }
