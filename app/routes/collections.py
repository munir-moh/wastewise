from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import CollectionRequest, CollectionStatus, User, Role
from app.utils import get_current_user, save_images, create_notification, roles_required

collections_bp = Blueprint("collections", __name__)


@collections_bp.post("/")
@jwt_required()
@roles_required("HOUSEHOLD")
def create_request():
    user = get_current_user()
    data = request.form if request.files else request.get_json() or {}

    if not data.get("address"):
        return jsonify({"message": "address is required"}), 400

    waste_types = data.get("waste_types", [])
    if isinstance(waste_types, str):
        waste_types = [waste_types]

    image_urls   = save_images(request.files.getlist("images"))
    scheduled_at = datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None

    req = CollectionRequest(
        household_id=user.id,
        waste_types=",".join(waste_types),
        description=data.get("description"),
        image_urls=",".join(image_urls),
        address=data["address"],
        latitude=float(data["latitude"]) if data.get("latitude") else None,
        longitude=float(data["longitude"]) if data.get("longitude") else None,
        scheduled_at=scheduled_at,
        household_note=data.get("household_note"),
    )
    db.session.add(req)
    db.session.commit()
    return jsonify(req.to_dict()), 201


@collections_bp.get("/my")
@jwt_required()
@roles_required("HOUSEHOLD")
def get_my_requests():
    user   = get_current_user()
    status = request.args.get("status")
    query  = CollectionRequest.query.filter_by(household_id=user.id)
    if status:
        query = query.filter_by(status=CollectionStatus(status))
    results = query.order_by(CollectionRequest.created_at.desc()).all()
    return jsonify([r.to_dict() for r in results])


@collections_bp.put("/<int:req_id>/cancel")
@jwt_required()
@roles_required("HOUSEHOLD")
def cancel_request(req_id):
    user = get_current_user()
    req  = db.get_or_404(CollectionRequest, req_id)

    if req.household_id != user.id:
        return jsonify({"message": "Forbidden"}), 403
    if req.status != CollectionStatus.PENDING:
        return jsonify({"message": "Only PENDING requests can be cancelled"}), 400

    req.status = CollectionStatus.CANCELLED
    db.session.commit()
    return jsonify(req.to_dict())


@collections_bp.get("/available")
@jwt_required()
@roles_required("COLLECTOR")
def get_available():
    collector = get_current_user()
    query = CollectionRequest.query.filter_by(status=CollectionStatus.PENDING, collector_id=None)
    if collector.lga:
        query = query.join(CollectionRequest.household).filter(User.lga == collector.lga)
    results = query.order_by(CollectionRequest.created_at.asc()).all()
    return jsonify([r.to_dict() for r in results])


@collections_bp.get("/assigned")
@jwt_required()
@roles_required("COLLECTOR")
def get_assigned():
    collector = get_current_user()
    results = CollectionRequest.query.filter(
        CollectionRequest.collector_id == collector.id,
        CollectionRequest.status.notin_([CollectionStatus.CANCELLED, CollectionStatus.COLLECTED]),
    ).order_by(CollectionRequest.scheduled_at.asc()).all()
    return jsonify([r.to_dict() for r in results])


@collections_bp.put("/<int:req_id>/accept")
@jwt_required()
@roles_required("COLLECTOR")
def accept_request(req_id):
    collector = get_current_user()
    req = db.get_or_404(CollectionRequest, req_id)

    if req.status != CollectionStatus.PENDING:
        return jsonify({"message": "Request is no longer available"}), 400

    req.collector_id = collector.id
    req.status = CollectionStatus.ACCEPTED
    create_notification(
        user_id=req.household_id,
        title="Collection Accepted",
        body="A collector has accepted your waste collection request.",
        type_="COLLECTION_UPDATE",
        ref_id=req.id,
    )
    db.session.commit()
    return jsonify(req.to_dict())


@collections_bp.put("/<int:req_id>/status")
@jwt_required()
@roles_required("COLLECTOR")
def update_status(req_id):
    collector = get_current_user()
    req  = db.get_or_404(CollectionRequest, req_id)
    data = request.get_json()

    if req.collector_id != collector.id:
        return jsonify({"message": "Forbidden"}), 403

    new_status = data.get("status")
    if new_status not in ("EN_ROUTE", "COLLECTED", "CANCELLED"):
        return jsonify({"message": "Invalid status"}), 400

    req.status = CollectionStatus(new_status)
    if data.get("collector_note"):
        req.collector_note = data["collector_note"]
    if new_status == "COLLECTED":
        req.collected_at = datetime.now(timezone.utc)
        req.household.points += 10

    messages = {
        "EN_ROUTE":  "Your collector is on the way!",
        "COLLECTED": "Your waste has been collected. Thank you for recycling!",
        "CANCELLED": "Your collection request was cancelled by the collector.",
    }
    create_notification(
        user_id=req.household_id,
        title=f"Collection {new_status.replace('_', ' ')}",
        body=messages[new_status],
        type_="COLLECTION_UPDATE",
        ref_id=req.id,
    )
    db.session.commit()
    return jsonify(req.to_dict())


@collections_bp.get("/")
@jwt_required()
@roles_required("SUPER_ADMIN", "COMMUNITY_ADMIN")
def get_all():
    user   = get_current_user()
    status = request.args.get("status")
    lga    = request.args.get("lga")
    page   = int(request.args.get("page", 1))
    limit  = int(request.args.get("limit", 30))

    query = CollectionRequest.query
    if status:
        query = query.filter_by(status=CollectionStatus(status))
    if lga:
        query = query.join(CollectionRequest.household).filter(User.lga == lga)
    elif user.role == Role.COMMUNITY_ADMIN and user.admin_lga:
        query = query.join(CollectionRequest.household).filter(User.lga == user.admin_lga)

    total   = query.count()
    results = query.order_by(CollectionRequest.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return jsonify({"data": [r.to_dict() for r in results], "total": total, "page": page})