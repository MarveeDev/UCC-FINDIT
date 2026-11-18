import os

from flask import Flask

from app.config import config_by_name, ensure_secure_secrets
from app.extensions import cors, db, jwt, migrate


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Resolve secrets from the live environment at startup, then enforce
    # production secret strength before serving any request.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", app.config.get("SECRET_KEY"))
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY", app.config.get("SECRET_KEY")
    )
    ensure_secure_secrets(app.config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}
    )

    _register_jwt_handlers(app)
    _register_blueprints(app)
    _register_models()
    _register_error_handlers(app)

    return app


def _register_blueprints(app):
    from app.admin.routes import admin_bp
    from app.analytics.routes import analytics_bp
    from app.audit.routes import audit_bp
    from app.auth.routes import auth_bp
    from app.claims.routes import claims_bp, handover_bp
    from app.custody.routes import custody_bp
    from app.feed.routes import feed_bp
    from app.health import health_bp
    from app.inspections.routes import inspections_bp
    from app.items.routes import items_bp
    from app.locations.routes import locations_bp
    from app.matching.routes import matches_bp
    from app.notifications.routes import notifications_bp
    from app.qr.routes import qr_bp
    from app.staff.routes import staff_bp
    from app.uploads.routes import uploads_bp
    from app.users.routes import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(claims_bp)
    app.register_blueprint(handover_bp)
    app.register_blueprint(qr_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(inspections_bp)
    app.register_blueprint(custody_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)


def _register_models():
    # Importing the model modules ensures they are registered with SQLAlchemy
    # (and therefore visible to Flask-Migrate's autogenerate).
    from app.users import models  # noqa: F401
    from app.locations import models  # noqa: F401
    from app.items import models  # noqa: F401
    from app.matching import models  # noqa: F401
    from app.claims import models  # noqa: F401
    from app.qr import models  # noqa: F401
    from app.notifications import models  # noqa: F401
    from app.security import models  # noqa: F401
    from app.inspections import models  # noqa: F401
    from app.custody import models  # noqa: F401
    from app.audit import models  # noqa: F401


def _register_jwt_handlers(app):
    from app.utils import fail

    @jwt.unauthorized_loader
    def _missing_token(_reason):
        return fail("Authentication required", status=401)

    @jwt.invalid_token_loader
    def _invalid_token(_reason):
        return fail("Invalid or expired token", status=401)

    @jwt.expired_token_loader
    def _expired_token(_jwt_header, _jwt_payload):
        return fail("Token has expired", status=401)


def _register_error_handlers(app):
    from app.utils import register_error_handlers

    register_error_handlers(app)
