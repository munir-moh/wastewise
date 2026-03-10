import os
import uuid
from functools import wraps
from flask import current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app.extensions import db
from app.models import User, Notification


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = db.session.get(User, user_id)
            if not user or user.role.value not in roles:
                from flask import jsonify
                return jsonify({"message": "Access denied"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    user_id = get_jwt_identity()
    return db.session.get(User, user_id)


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if not file or not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = current_app.config["UPLOAD_FOLDER"]
    file.save(os.path.join(folder, filename))
    return f"/uploads/{filename}"

def save_images(files):
    return [url for f in files if (url := save_image(f))]


def create_notification(user_id, title, body, type_=None, ref_id=None):
    notif = Notification(
        user_id=user_id,
        title=title,
        body=body,
        type=type_,
        ref_id=str(ref_id) if ref_id else None,
    )
    db.session.add(notif)