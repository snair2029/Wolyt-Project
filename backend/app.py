from flask import Flask, jsonify, request

app = Flask(__name__)

# Home route
@app.route("/")
def home():
    return jsonify({"message": "Wolyt backend is running!"})

# Transaction route (dummy example)
@app.route("/transaction", methods=["POST"])
def transaction():
    # Example: pretend we processed a payment
    data = request.get_json()  # Get input data from user
    amount = data.get("amount", 0)
    sender = data.get("sender", "unknown")
    receiver = data.get("receiver", "unknown")

    return jsonify({
        "status": "success",
        "message": f"Transaction of ${amount} from {sender} to {receiver} completed.",
        "trust_score_update": "User trust score recalculated (dummy)"
    })

if __name__ == "__main__":
    app.run(debug=True, port=5050)

