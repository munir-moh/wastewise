from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import Notification
from app.utils import get_current_user

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("/")
@jwt_required()
def get_notifications():
    user        = get_current_user()
    unread_only = request.args.get("unread_only") == "true"

    query = Notification.query.filter_by(user_id=user.id)
    if unread_only:
        query = query.filter_by(is_read=False)

    results      = query.order_by(Notification.created_at.desc()).limit(50).all()
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({"data": [n.to_dict() for n in results], "unread_count": unread_count})


@notifications_bp.put("/read-all")
@jwt_required()
def mark_all_read():
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All notifications marked as read"})


@notifications_bp.put("/<int:notif_id>/read")
@jwt_required()
def mark_one_read(notif_id):
    user  = get_current_user()
    notif = db.get_or_404(Notification, notif_id)
    if notif.user_id != user.id:
        return jsonify({"message": "Forbidden"}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({"message": "Notification marked as read"})