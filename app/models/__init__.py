from app.extensions import db
from datetime import datetime, timezone
import enum


class Role(str, enum.Enum):
    HOUSEHOLD       = "HOUSEHOLD"
    COLLECTOR       = "COLLECTOR"
    COMMUNITY_ADMIN = "COMMUNITY_ADMIN"
    SUPER_ADMIN     = "SUPER_ADMIN"

class WasteType(str, enum.Enum):
    GENERAL = "GENERAL"
    PAPER   = "PAPER"
    PLASTIC = "PLASTIC"
    GLASS   = "GLASS"
    METAL   = "METAL"
    ORGANIC = "ORGANIC"
    E_WASTE = "E_WASTE"

class CollectionStatus(str, enum.Enum):
    PENDING   = "PENDING"
    ACCEPTED  = "ACCEPTED"
    EN_ROUTE  = "EN_ROUTE"
    COLLECTED = "COLLECTED"
    CANCELLED = "CANCELLED"

class DumpStatus(str, enum.Enum):
    OPEN     = "OPEN"
    REVIEWED = "REVIEWED"
    RESOLVED = "RESOLVED"

class ResourceType(str, enum.Enum):
    ARTICLE     = "ARTICLE"
    INFOGRAPHIC = "INFOGRAPHIC"
    VIDEO       = "VIDEO"
    FAQ         = "FAQ"


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    phone      = db.Column(db.String(20))
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.Enum(Role), default=Role.HOUSEHOLD, nullable=False)
    avatar_url = db.Column(db.String(300))
    points     = db.Column(db.Integer, default=0)

    address   = db.Column(db.String(300))
    latitude  = db.Column(db.Float)
    longitude = db.Column(db.Float)
    lga       = db.Column(db.String(100))
    state     = db.Column(db.String(100), default="Lagos")

    service_radius       = db.Column(db.Float)
    service_area         = db.Column(db.String(300))
    accepted_waste_types = db.Column(db.String(200), default="")
    is_available         = db.Column(db.Boolean, default=True)

    admin_lga  = db.Column(db.String(100))
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    collection_requests = db.relationship("CollectionRequest", foreign_keys="CollectionRequest.household_id", backref="household", lazy=True)
    assigned_requests   = db.relationship("CollectionRequest", foreign_keys="CollectionRequest.collector_id", backref="collector", lazy=True)
    dump_reports        = db.relationship("DumpReport", backref="reporter", lazy=True)
    notifications       = db.relationship("Notification", backref="user", lazy=True)
    announcements       = db.relationship("Announcement", backref="author", lazy=True)

    def to_dict(self):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role.value,
            "avatar_url": self.avatar_url,
            "points": self.points,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "lga": self.lga,
            "state": self.state,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }
        if self.role == Role.COLLECTOR:
            data.update({
                "service_radius": self.service_radius,
                "service_area": self.service_area,
                "accepted_waste_types": self.accepted_waste_types.split(",") if self.accepted_waste_types else [],
                "is_available": self.is_available,
            })
        if self.role == Role.COMMUNITY_ADMIN:
            data["admin_lga"] = self.admin_lga
        return data


class CollectionRequest(db.Model):
    __tablename__ = "collection_requests"

    id             = db.Column(db.Integer, primary_key=True)
    waste_types    = db.Column(db.String(200), nullable=False)
    description    = db.Column(db.Text)
    image_urls     = db.Column(db.Text, default="")
    status         = db.Column(db.Enum(CollectionStatus), default=CollectionStatus.PENDING)
    scheduled_at   = db.Column(db.DateTime)
    collected_at   = db.Column(db.DateTime)

    address        = db.Column(db.String(300), nullable=False)
    latitude       = db.Column(db.Float)
    longitude      = db.Column(db.Float)

    household_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    collector_id   = db.Column(db.Integer, db.ForeignKey("users.id"))

    collector_note = db.Column(db.Text)
    household_note = db.Column(db.Text)

    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "waste_types": self.waste_types.split(",") if self.waste_types else [],
            "description": self.description,
            "image_urls": self.image_urls.split(",") if self.image_urls else [],
            "status": self.status.value,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "household_id": self.household_id,
            "collector_id": self.collector_id,
            "collector_note": self.collector_note,
            "household_note": self.household_note,
            "created_at": self.created_at.isoformat(),
            "household": self.household.to_dict() if self.household else None,
            "collector": self.collector.to_dict() if self.collector else None,
        }


class RecyclingCenter(db.Model):
    __tablename__ = "recycling_centers"

    id                 = db.Column(db.Integer, primary_key=True)
    name               = db.Column(db.String(150), nullable=False)
    address            = db.Column(db.String(300), nullable=False)
    latitude           = db.Column(db.Float)
    longitude          = db.Column(db.Float)
    lga                = db.Column(db.String(100))
    state              = db.Column(db.String(100), default="Lagos")
    phone              = db.Column(db.String(20))
    email              = db.Column(db.String(120))
    website            = db.Column(db.String(200))
    opening_hours      = db.Column(db.String(200))
    accepted_materials = db.Column(db.String(200), default="")
    description        = db.Column(db.Text)
    image_url          = db.Column(db.String(300))
    is_verified        = db.Column(db.Boolean, default=False)
    is_active          = db.Column(db.Boolean, default=True)
    created_at         = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "lga": self.lga,
            "state": self.state,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "opening_hours": self.opening_hours,
            "accepted_materials": self.accepted_materials.split(",") if self.accepted_materials else [],
            "description": self.description,
            "image_url": self.image_url,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


class DumpReport(db.Model):
    __tablename__ = "dump_reports"

    id          = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    image_urls  = db.Column(db.Text, default="")
    address     = db.Column(db.String(300), nullable=False)
    latitude    = db.Column(db.Float)
    longitude   = db.Column(db.Float)
    lga         = db.Column(db.String(100))
    status      = db.Column(db.Enum(DumpStatus), default=DumpStatus.OPEN)
    admin_note  = db.Column(db.Text)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "image_urls": self.image_urls.split(",") if self.image_urls else [],
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "lga": self.lga,
            "status": self.status.value,
            "admin_note": self.admin_note,
            "reporter_id": self.reporter_id,
            "reporter": self.reporter.to_dict() if self.reporter else None,
            "created_at": self.created_at.isoformat(),
        }


class Resource(db.Model):
    __tablename__ = "resources"

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    content      = db.Column(db.Text, nullable=False)
    summary      = db.Column(db.String(400))
    type         = db.Column(db.Enum(ResourceType), default=ResourceType.ARTICLE)
    image_url    = db.Column(db.String(300))
    video_url    = db.Column(db.String(300))
    tags         = db.Column(db.String(300), default="")
    is_published = db.Column(db.Boolean, default=False)
    views        = db.Column(db.Integer, default=0)
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "type": self.type.value,
            "image_url": self.image_url,
            "video_url": self.video_url,
            "tags": self.tags.split(",") if self.tags else [],
            "is_published": self.is_published,
            "views": self.views,
            "created_at": self.created_at.isoformat(),
        }


class Announcement(db.Model):
    __tablename__ = "announcements"

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    lga        = db.Column(db.String(100))
    author_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "lga": self.lga,
            "author_id": self.author_id,
            "author": {"id": self.author.id, "name": self.author.name, "role": self.author.role.value} if self.author else None,
            "created_at": self.created_at.isoformat(),
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    type       = db.Column(db.String(50))
    ref_id     = db.Column(db.String(50))
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "is_read": self.is_read,
            "type": self.type,
            "ref_id": self.ref_id,
            "created_at": self.created_at.isoformat(),
        }