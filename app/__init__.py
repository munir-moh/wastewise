import os
from flask import Flask
from dotenv import load_dotenv
from app.extensions import db, jwt

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"]                     = os.getenv("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET_KEY"]                 = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["SQLALCHEMY_DATABASE_URI"]        = os.getenv("DATABASE_URL", "sqlite:///wastewise.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"]                  = os.getenv("UPLOAD_FOLDER", "uploads")
    app.config["MAX_CONTENT_LENGTH"]             = 5 * 1024 * 1024  # 5MB

    db.init_app(app)
    jwt.init_app(app)

    from flask_cors import CORS
    CORS(app)

    from app.routes.auth          import auth_bp
    from app.routes.collections   import collections_bp
    from app.routes.centers       import centers_bp
    from app.routes.dumps         import dumps_bp
    from app.routes.resources     import resources_bp
    from app.routes.announcements import announcements_bp
    from app.routes.notifications import notifications_bp
    from app.routes.admin         import admin_bp

    app.register_blueprint(auth_bp,          url_prefix="/api/auth")
    app.register_blueprint(collections_bp,   url_prefix="/api/collections")
    app.register_blueprint(centers_bp,       url_prefix="/api/recycling-centers")
    app.register_blueprint(dumps_bp,         url_prefix="/api/dump-reports")
    app.register_blueprint(resources_bp,     url_prefix="/api/resources")
    app.register_blueprint(announcements_bp, url_prefix="/api/announcements")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(admin_bp,         url_prefix="/api/admin")

    @app.get("/health")
    def health():
        return {"status": "OK", "app": "WasteWise Nigeria"}

    # Serve uploaded images
    from flask import send_from_directory
    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    with app.app_context():
        db.create_all()
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app