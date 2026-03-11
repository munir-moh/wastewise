from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import Announcement, Role
from app.utils import get_current_user, roles_required

announcements_bp = Blueprint("announcements", __name__)


@announcements_bp.get("/")
@jwt_required()
def get_announcements():
    user  = get_current_user()
    page  = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    query = Announcement.query.filter(
        db.or_(Announcement.lga == None, Announcement.lga == user.lga)
    )
    total   = query.count()
    results = query.order_by(Announcement.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return jsonify({"data": [a.to_dict() for a in results], "total": total, "page": page})


@announcements_bp.post("/")
@jwt_required()
@roles_required("SUPER_ADMIN", "COMMUNITY_ADMIN")
def create_announcement():
    user = get_current_user()
    data = request.get_json()
    lga  = user.admin_lga if user.role == Role.COMMUNITY_ADMIN else data.get("lga")

    ann = Announcement(title=data["title"], body=data["body"], lga=lga, author_id=user.id)
    db.session.add(ann)
    db.session.commit()
    return jsonify(ann.to_dict()), 201


@announcements_bp.delete("/<int:ann_id>")
@jwt_required()
@roles_required("SUPER_ADMIN")
def delete_announcement(ann_id):
    ann = db.get_or_404(Announcement, ann_id)
    db.session.delete(ann)
    db.session.commit()
    return jsonify({"message": "Announcement deleted"})