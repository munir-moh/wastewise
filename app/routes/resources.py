from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import Resource, ResourceType
from app.utils import save_image, roles_required

resources_bp = Blueprint("resources", __name__)


@resources_bp.get("/")
def get_resources():
    type_  = request.args.get("type")
    search = request.args.get("search")
    page   = int(request.args.get("page", 1))
    limit  = int(request.args.get("limit", 20))

    query = Resource.query.filter_by(is_published=True)
    if type_:
        query = query.filter_by(type=ResourceType(type_))
    if search:
        query = query.filter(Resource.title.ilike(f"%{search}%"))

    total   = query.count()
    results = query.order_by(Resource.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return jsonify({"data": [r.to_dict() for r in results], "total": total, "page": page})


@resources_bp.get("/<int:resource_id>")
def get_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    resource.views += 1
    db.session.commit()
    return jsonify(resource.to_dict())


@resources_bp.post("/")
@jwt_required()
@roles_required("SUPER_ADMIN")
def create_resource():
    data = request.form if request.files else request.get_json() or {}
    tags = data.get("tags", [])

    resource = Resource(
        title=data["title"],
        content=data["content"],
        summary=data.get("summary"),
        type=ResourceType(data.get("type", "ARTICLE")),
        video_url=data.get("video_url"),
        tags=",".join(tags) if isinstance(tags, list) else tags,
        is_published=str(data.get("is_published", "false")).lower() == "true",
        image_url=save_image(request.files.get("image")),
    )
    db.session.add(resource)
    db.session.commit()
    return jsonify(resource.to_dict()), 201


@resources_bp.put("/<int:resource_id>")
@jwt_required()
@roles_required("SUPER_ADMIN")
def update_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    data = request.form if request.files else request.get_json() or {}

    for field in ("title", "content", "summary", "video_url"):
        if field in data:
            setattr(resource, field, data[field])
    if "type" in data:
        resource.type = ResourceType(data["type"])
    if "tags" in data:
        t = data["tags"]
        resource.tags = ",".join(t) if isinstance(t, list) else t
    if "is_published" in data:
        resource.is_published = str(data["is_published"]).lower() == "true"
    if "image" in request.files:
        url = save_image(request.files["image"])
        if url:
            resource.image_url = url

    db.session.commit()
    return jsonify(resource.to_dict())


@resources_bp.delete("/<int:resource_id>")
@jwt_required()
@roles_required("SUPER_ADMIN")
def delete_resource(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    db.session.delete(resource)
    db.session.commit()
    return jsonify({"message": "Resource deleted"})