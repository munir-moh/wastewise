from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models import User, Role
from app.utils import get_current_user, save_image

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json()

    for field in ["name", "email", "password"]:
        if not data.get(field):
            return jsonify({"message": f"{field} is required"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already registered"}), 409

    role_value = data.get("role", "HOUSEHOLD")
    if role_value not in ("HOUSEHOLD", "COLLECTOR"):
        role_value = "HOUSEHOLD"

    user = User(
        name=data["name"],
        email=data["email"].lower().strip(),
        password=generate_password_hash(data["password"]),
        role=Role(role_value),
        phone=data.get("phone"),
        address=data.get("address"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        lga=data.get("lga"),
        state=data.get("state", "Lagos"),
        service_radius=data.get("service_radius"),
        service_area=data.get("service_area"),
        accepted_waste_types=",".join(data.get("accepted_waste_types", [])),
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email", "").lower()).first()

    if not user or not user.is_active or not check_password_hash(user.password, data.get("password", "")):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(identity=user.id)
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def get_me():
    return jsonify(get_current_user().to_dict())


@auth_bp.put("/me")
@jwt_required()
def update_me():
    user = get_current_user()
    data = request.form if request.files else request.get_json() or {}

    for field in ("name", "phone", "address", "lga", "state", "service_area"):
        if field in data:
            setattr(user, field, data[field])

    for field in ("latitude", "longitude", "service_radius"):
        if field in data:
            setattr(user, field, float(data[field]))

    if "accepted_waste_types" in data:
        types = data["accepted_waste_types"]
        user.accepted_waste_types = ",".join(types) if isinstance(types, list) else types

    if "is_available" in data:
        user.is_available = str(data["is_available"]).lower() == "true"

    if "avatar" in request.files:
        url = save_image(request.files["avatar"])
        if url:
            user.avatar_url = url

    db.session.commit()
    return jsonify(user.to_dict())


@auth_bp.put("/change-password")
@jwt_required()
def change_password():
    user = get_current_user()
    data = request.get_json()

    if not check_password_hash(user.password, data.get("current_password", "")):
        return jsonify({"message": "Current password is incorrect"}), 400

    user.password = generate_password_hash(data["new_password"])
    db.session.commit()
    return jsonify({"message": "Password updated successfully"})