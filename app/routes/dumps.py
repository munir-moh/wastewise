from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import DumpReport, DumpStatus, Role
from app.utils import get_current_user, save_images, create_notification, roles_required

dumps_bp = Blueprint("dumps", __name__)


@dumps_bp.post("/")
@jwt_required()
def create_report():
    user = get_current_user()
    data = request.form if request.files else request.get_json() or {}

    if not data.get("description") or not data.get("address"):
        return jsonify({"message": "description and address are required"}), 400

    image_urls = save_images(request.files.getlist("images"))
    report = DumpReport(
        reporter_id=user.id,
        description=data["description"],
        address=data["address"],
        latitude=float(data["latitude"]) if data.get("latitude") else None,
        longitude=float(data["longitude"]) if data.get("longitude") else None,
        lga=data.get("lga") or user.lga,
        image_urls=",".join(image_urls),
    )
    db.session.add(report)
    db.session.commit()
    return jsonify(report.to_dict()), 201


@dumps_bp.get("/my")
@jwt_required()
def get_my_reports():
    user = get_current_user()
    results = DumpReport.query.filter_by(reporter_id=user.id).order_by(DumpReport.created_at.desc()).all()
    return jsonify([r.to_dict() for r in results])


@dumps_bp.get("/")
@jwt_required()
@roles_required("SUPER_ADMIN", "COMMUNITY_ADMIN")
def get_all_reports():
    user   = get_current_user()
    status = request.args.get("status")
    lga    = request.args.get("lga")
    page   = int(request.args.get("page", 1))
    limit  = int(request.args.get("limit", 30))

    query = DumpReport.query
    if status:
        query = query.filter_by(status=DumpStatus(status))
    if user.role == Role.COMMUNITY_ADMIN:
        query = query.filter_by(lga=user.admin_lga)
    elif lga:
        query = query.filter_by(lga=lga)

    total   = query.count()
    results = query.order_by(DumpReport.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return jsonify({"data": [r.to_dict() for r in results], "total": total, "page": page})


@dumps_bp.put("/<int:report_id>/status")
@jwt_required()
@roles_required("SUPER_ADMIN", "COMMUNITY_ADMIN")
def update_status(report_id):
    report = db.get_or_404(DumpReport, report_id)
    data   = request.get_json()
    status = data.get("status")

    if status not in ("REVIEWED", "RESOLVED"):
        return jsonify({"message": "Invalid status"}), 400

    report.status = DumpStatus(status)
    if data.get("admin_note"):
        report.admin_note = data["admin_note"]

    create_notification(
        user_id=report.reporter_id,
        title=f"Dump Report {status}",
        body=f"Your illegal dumping report has been marked as {status.lower()}.",
        type_="REPORT_UPDATE",
        ref_id=report.id,
    )
    db.session.commit()
    return jsonify(report.to_dict())