from flask_cors import CORS
from flask import Flask, request, jsonify
from sqlalchemy.orm import Session
from contextlib import contextmanager
import secrets
import uuid
import os

from database import engine, SessionLocal
from models import Base, Merchant, Resource, Session as PaymentSession

app = Flask(__name__)
CORS(app)

# ✅ Create all DB tables
Base.metadata.create_all(bind=engine)

# ✅ SAFE DB SESSION HANDLER (PREVENTS POOL CRASH)
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ Auto-create a demo merchant if none exists
def create_demo_merchant():
    with get_db() as db:
        merchant = db.query(Merchant).first()
        if not merchant:
            demo = Merchant(
                name="Demo Merchant",
                api_key=secrets.token_hex(16),
                wallet_address="DEMO_QUBIC_WALLET"
            )
            db.add(demo)
            db.commit()
            print("✅ Demo merchant created")
            print("🔑 API KEY:", demo.api_key)


create_demo_merchant()


# ✅ Health check
@app.get("/")
def home():
    return jsonify({
        "success": True,
        "status": "QubiPay backend running"
    })


# ✅ Create a new billable resource
@app.post("/api/resources")
def create_resource():
    data = request.json or {}

    api_key = data.get("api_key")
    name = data.get("name")
    description = data.get("description", "")
    price_qubic = data.get("price_qubic")

    if not api_key or not name or price_qubic is None:
        return jsonify({
            "success": False,
            "error": "Missing required fields"
        }), 400

    if int(price_qubic) <= 0:
        return jsonify({
            "success": False,
            "error": "Price must be greater than 0"
        }), 400

    with get_db() as db:
        merchant = db.query(Merchant).filter_by(api_key=api_key).first()
        if not merchant:
            return jsonify({
                "success": False,
                "error": "Invalid API key"
            }), 401

        # ✅ Prevent duplicate resource names
        existing = db.query(Resource).filter_by(
            merchant_id=merchant.id,
            name=name
        ).first()

        if existing:
            return jsonify({
                "success": False,
                "error": "Resource already exists"
            }), 400

        resource = Resource(
            merchant_id=merchant.id,
            name=name,
            description=description,
            price_qubic=price_qubic
        )

        db.add(resource)
        db.commit()

        return jsonify({
            "success": True,
            "data": {
                "id": resource.id,
                "name": resource.name,
                "description": resource.description,
                "price_qubic": resource.price_qubic
            }
        })


# ✅ List all resources for a merchant
@app.get("/api/resources")
def list_resources():
    api_key = request.args.get("api_key")

    if not api_key:
        return jsonify({
            "success": False,
            "error": "API key required"
        }), 400

    with get_db() as db:
        merchant = db.query(Merchant).filter_by(api_key=api_key).first()
        if not merchant:
            return jsonify({
                "success": False,
                "error": "Invalid API key"
            }), 401

        resources = db.query(Resource).filter_by(merchant_id=merchant.id).all()

        output = []
        for r in resources:
            output.append({
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "price_qubic": r.price_qubic
            })

        return jsonify({
            "success": True,
            "data": output
        })


# ✅ Create Pay-Per-Use Payment Session
@app.post("/api/pay-per-use")
def create_payment_session():
    data = request.json or {}

    api_key = data.get("api_key")
    resource_id = data.get("resource_id")
    user_wallet = data.get("user_wallet")

    if not api_key or not resource_id or not user_wallet:
        return jsonify({
            "success": False,
            "error": "Missing required fields"
        }), 400

    with get_db() as db:
        merchant = db.query(Merchant).filter_by(api_key=api_key).first()
        if not merchant:
            return jsonify({
                "success": False,
                "error": "Invalid API key"
            }), 401

        resource = db.query(Resource).filter_by(
            id=resource_id,
            merchant_id=merchant.id
        ).first()

        if not resource:
            return jsonify({
                "success": False,
                "error": "Invalid resource"
            }), 404

        session_id = str(uuid.uuid4())

        session = PaymentSession(
            id=session_id,
            resource_id=resource.id,
            user_wallet=user_wallet,
            amount_qubic=resource.price_qubic,
            status="pending"
        )

        db.add(session)
        db.commit()

        return jsonify({
            "success": True,
            "data": {
                "session_id": session.id,
                "amount_qubic": session.amount_qubic,
                "pay_to_wallet": merchant.wallet_address,
                "status": session.status
            }
        })


# ✅ Get Payment Session Status
@app.get("/api/sessions/<session_id>")
def get_session_status(session_id):
    with get_db() as db:
        session = db.query(PaymentSession).filter_by(id=session_id).first()
        if not session:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404

        return jsonify({
            "success": True,
            "data": {
                "session_id": session.id,
                "resource_id": session.resource_id,
                "user_wallet": session.user_wallet,
                "amount_qubic": session.amount_qubic,
                "status": session.status
            }
        })


# ✅ DEMO ONLY: Mark Payment as Paid
@app.post("/api/sessions/<session_id>/mock-paid")
def mark_session_paid(session_id):
    with get_db() as db:
        session = db.query(PaymentSession).filter_by(id=session_id).first()
        if not session:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404

        session.status = "paid"
        db.commit()

        return jsonify({
            "success": True,
            "data": {
                "message": "Payment marked as PAID (demo)",
                "session_id": session.id,
                "status": session.status
            }
        })

@app.get("/api/sessions/all")
def get_all_sessions():
    with get_db() as db:
        sessions = db.query(PaymentSession).all()
        return jsonify([
            {
                "session_id": s.id,
                "amount_qubic": s.amount_qubic,
                "status": s.status
            } for s in sessions
        ])


# ✅ Global crash protection
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "details": str(e)
    }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=5000)
