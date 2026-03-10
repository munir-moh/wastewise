from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import RecyclingCenter
from app.utils import save_image, roles_required

centers_bp = Blueprint("centers", __name__)


@centers_bp.get("/")
def get_centers():
    lga      = request.args.get("lga")
    material = request.args.get("material")
    page     = int(request.args.get("page", 1))
    limit    = int(request.args.get("limit", 20))

    query = RecyclingCenter.query.filter_by(is_active=True)
    if lga:
        query = query.filter_by(lga=lga)
    if material:
        query = query.filter(RecyclingCenter.accepted_materials.contains(material))

    total   = query.count()
    results = query.order_by(RecyclingCenter.name).offset((page-1)*limit).limit(limit).all()
    return jsonify({"data": [c.to_dict() for c in results], "total": total, "page": page})


@centers_bp.get("/<int:center_id>")
def get_center(center_id):
    return jsonify(db.get_or_404(RecyclingCenter, center_id).to_dict())


@centers_bp.post("/")
@jwt_required()
@roles_required("SUPER_ADMIN")
def create_center():
    data      = request.form if request.files else request.get_json() or {}
    materials = data.get("accepted_materials", [])

    center = RecyclingCenter(
        name=data["name"],
        address=data["address"],
        latitude=float(data["latitude"]) if data.get("latitude") else None,
        longitude=float(data["longitude"]) if data.get("longitude") else None,
        lga=data.get("lga"),
        state=data.get("state", "Lagos"),
        phone=data.get("phone"),
        email=data.get("email"),
        website=data.get("website"),
        opening_hours=data.get("opening_hours"),
        accepted_materials=",".join(materials) if isinstance(materials, list) else materials,
        description=data.get("description"),
        image_url=save_image(request.files.get("image")),
    )
    db.session.add(center)
    db.session.commit()
    return jsonify(center.to_dict()), 201


@centers_bp.put("/<int:center_id>")
@jwt_required()
@roles_required("SUPER_ADMIN")
def update_center(center_id):
    center = db.get_or_404(RecyclingCenter, center_id)
    data   = request.form if request.files else request.get_json() or {}

    for field in ("name", "address", "lga", "state", "phone", "email", "website", "opening_hours", "description"):
        if field in data:
            setattr(center, field, data[field])
    for field in ("latitude", "longitude"):
        if field in data:
            setattr(center, field, float(data[field]))
    if "accepted_materials" in data:
        m = data["accepted_materials"]
        center.accepted_materials = ",".join(m) if isinstance(m, list) else m
    if "is_verified" in data:
        center.is_verified = str(data["is_verified"]).lower() == "true"
    if "is_active" in data:
        center.is_active = str(data["is_active"]).lower() == "true"
    if "image" in request.files:
        url = save_image(request.files["image"])
        if url:
            center.image_url = url

    db.session.commit()
    return jsonify(center.to_dict())


@centers_bp.delete("/<int:center_id>")
@jwt_required()
@roles_required("SUPER_ADMIN")
def delete_center(center_id):
    center = db.get_or_404(RecyclingCenter, center_id)
    center.is_active = False
    db.session.commit()
    return jsonify({"message": "Recycling center deactivated"})