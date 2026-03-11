from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import User, Role, CollectionRequest, CollectionStatus, DumpReport, DumpStatus, RecyclingCenter
from app.utils import get_current_user, roles_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/users")
@jwt_required()
@roles_required("SUPER_ADMIN")
def get_users():
    role   = request.args.get("role")
    lga    = request.args.get("lga")
    search = request.args.get("search")
    page   = int(request.args.get("page", 1))
    limit  = int(request.args.get("limit", 30))

    query = User.query
    if role:
        query = query.filter_by(role=Role(role))
    if lga:
        query = query.filter_by(lga=lga)
    if search:
        query = query.filter(db.or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))

    total   = query.count()
    results = query.order_by(User.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return jsonify({"data": [u.to_dict() for u in results], "total": total, "page": page})


@admin_bp.put("/users/<int:user_id>/role")
@jwt_required()
@roles_required("SUPER_ADMIN")
def update_role(user_id):
    user = db.get_or_404(User, user_id)
    data = request.get_json()
    role = data.get("role")

    if role not in ("HOUSEHOLD", "COLLECTOR", "COMMUNITY_ADMIN"):
        return jsonify({"message": "Invalid role"}), 400

    user.role      = Role(role)
    user.admin_lga = data.get("admin_lga") if role == "COMMUNITY_ADMIN" else None
    db.session.commit()
    return jsonify(user.to_dict())


@admin_bp.put("/users/<int:user_id>/toggle-active")
@jwt_required()
@roles_required("SUPER_ADMIN")
def toggle_active(user_id):
    user           = db.get_or_404(User, user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({"id": user.id, "name": user.name, "is_active": user.is_active})


@admin_bp.get("/analytics")
@jwt_required()
@roles_required("SUPER_ADMIN", "COMMUNITY_ADMIN")
def get_analytics():
    current_user = get_current_user()
    lga_filter   = current_user.admin_lga if current_user.role == Role.COMMUNITY_ADMIN else request.args.get("lga")

    user_query = User.query.filter_by(is_active=True)
    if lga_filter:
        user_query = user_query.filter_by(lga=lga_filter)

    req_query = CollectionRequest.query
    if lga_filter:
        req_query = req_query.join(CollectionRequest.household).filter(User.lga == lga_filter)

    dump_query = DumpReport.query
    if lga_filter:
        dump_query = dump_query.filter_by(lga=lga_filter)

    collected_reqs  = req_query.filter(CollectionRequest.status == CollectionStatus.COLLECTED).all()
    waste_breakdown = {}
    for r in collected_reqs:
        for t in (r.waste_types or "").split(","):
            if t:
                waste_breakdown[t] = waste_breakdown.get(t, 0) + 1

    return jsonify({
        "users": {
            "total":      user_query.count(),
            "households": user_query.filter_by(role=Role.HOUSEHOLD).count(),
            "collectors": User.query.filter_by(role=Role.COLLECTOR, is_active=True).count(),
        },
        "collections": {
            "total":     req_query.count(),
            "pending":   req_query.filter(CollectionRequest.status == CollectionStatus.PENDING).count(),
            "collected": len(collected_reqs),
        },
        "dump_reports": {
            "open":     dump_query.filter_by(status=DumpStatus.OPEN).count(),
            "resolved": dump_query.filter_by(status=DumpStatus.RESOLVED).count(),
        },
        "recycling_centers": RecyclingCenter.query.filter_by(is_active=True).count(),
        "waste_breakdown": waste_breakdown,
    })


@admin_bp.get("/collectors")
@jwt_required()
@roles_required("SUPER_ADMIN", "COMMUNITY_ADMIN")
def get_collectors():
    lga     = request.args.get("lga")
    query   = User.query.filter_by(role=Role.COLLECTOR, is_active=True, is_available=True)
    if lga:
        query = query.filter_by(lga=lga)
    return jsonify([u.to_dict() for u in query.all()])