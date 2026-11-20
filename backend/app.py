import os
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app, origins=os.getenv("FRONTEND_ORIGIN", "*"))
db_path = os.getenv("DATABASE_URL", "sqlite:///foodbridge.db")
app.config["SQLALCHEMY_DATABASE_URI"] = db_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-in-production")
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), nullable=False)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    donor_name = db.Column(db.String(120), nullable=False)
    food_name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(220), nullable=False)
    use_by = db.Column(db.String(40), nullable=False)
    notes = db.Column(db.Text, default="")
    status = db.Column(db.String(40), default="Available")
    reserved_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reserved_name = db.Column(db.String(120), nullable=True)
    volunteer_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def user_payload(user):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

def current_user():
    uid = request.headers.get("X-User-Id")
    return db.session.get(User, int(uid)) if uid and uid.isdigit() else None

def require_user(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "Please sign in to continue."}), 401
        return fn(user, *args, **kwargs)
    return wrapper

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "FoodBridge API"})

@app.post("/api/register")
def register():
    data = request.get_json() or {}
    required = ["name", "email", "password", "role"]
    if any(not data.get(k) for k in required):
        return jsonify({"error": "Please complete all required fields."}), 400
    if data["role"] not in ["Restaurant Manager", "Retail Donor", "NGO Coordinator", "Collection Volunteer"]:
        return jsonify({"error": "Invalid role."}), 400
    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409
    user = User(name=data["name"].strip(), email=email,
                password=generate_password_hash(data["password"]), role=data["role"])
    db.session.add(user); db.session.commit()
    return jsonify({"user": user_payload(user)}), 201

@app.post("/api/login")
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=(data.get("email") or "").strip().lower()).first()
    if not user or not check_password_hash(user.password, data.get("password") or ""):
        return jsonify({"error": "Invalid email or password."}), 401
    return jsonify({"user": user_payload(user)})

@app.get("/api/donations")
def donations():
    rows = Donation.query.order_by(Donation.created_at.desc()).all()
    return jsonify([{
        "id": d.id, "donor_id": d.donor_id, "donor_name": d.donor_name,
        "food_name": d.food_name, "category": d.category, "quantity": d.quantity,
        "location": d.location, "use_by": d.use_by, "notes": d.notes,
        "status": d.status, "reserved_by": d.reserved_by,
        "reserved_name": d.reserved_name, "volunteer_name": d.volunteer_name
    } for d in rows])

@app.post("/api/donations")
@require_user
def create_donation(user):
    if user.role not in ["Restaurant Manager", "Retail Donor"]:
        return jsonify({"error": "Only donors can post food donations."}), 403
    data = request.get_json() or {}
    required = ["food_name", "category", "quantity", "location", "use_by"]
    if any(not data.get(k) for k in required):
        return jsonify({"error": "Please complete all donation details."}), 400
    d = Donation(donor_id=user.id, donor_name=user.name,
        food_name=data["food_name"], category=data["category"],
        quantity=data["quantity"], location=data["location"],
        use_by=data["use_by"], notes=data.get("notes", ""))
    db.session.add(d); db.session.commit()
    return jsonify({"id": d.id, "message": "Donation posted successfully."}), 201

@app.post("/api/donations/<int:donation_id>/reserve")
@require_user
def reserve(donation_id, user):
    if user.role != "NGO Coordinator":
        return jsonify({"error": "Only NGO Coordinators can reserve donations."}), 403
    d = db.session.get(Donation, donation_id)
    if not d: return jsonify({"error": "Donation not found."}), 404
    if d.status != "Available": return jsonify({"error": "This donation is no longer available."}), 409
    d.status, d.reserved_by, d.reserved_name = "Reserved", user.id, user.name
    db.session.commit()
    return jsonify({"message": "Donation reserved successfully."})

@app.post("/api/donations/<int:donation_id>/collect")
@require_user
def collect(donation_id, user):
    if user.role != "Collection Volunteer":
        return jsonify({"error": "Only Collection Volunteers can update collection."}), 403
    d = db.session.get(Donation, donation_id)
    if not d: return jsonify({"error": "Donation not found."}), 404
    if d.status != "Reserved": return jsonify({"error": "Only reserved donations can be collected."}), 409
    d.status, d.volunteer_name = "Collected", user.name
    db.session.commit()
    return jsonify({"message": "Collection marked as collected."})

@app.post("/api/donations/<int:donation_id>/complete")
@require_user
def complete(donation_id, user):
    if user.role not in ["NGO Coordinator", "Collection Volunteer"]:
        return jsonify({"error": "Only NGO Coordinators or Collection Volunteers can complete donations."}), 403
    d = db.session.get(Donation, donation_id)
    if not d: return jsonify({"error": "Donation not found."}), 404
    if d.status != "Collected": return jsonify({"error": "Donation must be collected first."}), 409
    d.status = "Completed"
    db.session.commit()
    return jsonify({"message": "Donation marked as completed."})

with app.app_context():
    db.create_all()
    # Small demo dataset appears on first launch.
    if Donation.query.count() == 0:
        demo = User.query.filter_by(email="demo.donor@foodbridge.test").first()
        if not demo:
            demo = User(name="Green Bowl Kitchen", email="demo.donor@foodbridge.test",
                password=generate_password_hash("demo123"), role="Restaurant Manager")
            db.session.add(demo); db.session.commit()
        db.session.add_all([
            Donation(donor_id=demo.id, donor_name=demo.name, food_name="Fresh vegetable rice",
                category="Prepared meals", quantity="18 meal boxes", location="Anna Nagar, Chennai",
                use_by="2026-11-21T13:30", notes="Packed this morning. Keep refrigerated."),
            Donation(donor_id=demo.id, donor_name=demo.name, food_name="Seasonal fruit basket",
                category="Fruits & vegetables", quantity="12 kg", location="Kilpauk, Chennai",
                use_by="2026-11-21T17:00", notes="Apples, bananas and oranges.")
        ])
        db.session.commit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
