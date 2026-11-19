from app import create_app
from app.uploads import cloudinary_service as svc


def _make_app(cloud_name="", api_key="", api_secret=""):
    app = create_app("development")
    app.config["CLOUDINARY_CLOUD_NAME"] = cloud_name
    app.config["CLOUDINARY_API_KEY"] = api_key
    app.config["CLOUDINARY_API_SECRET"] = api_secret
    return app


def _raise_auth(*a, **kw):
    raise svc.AuthorizationRequired("unauthorized")


def test_diagnostics_never_leaks_secret_values():
    app = _make_app(
        cloud_name="my-cloud",
        api_key="123456789012345",
        api_secret="abcdefghijklmnopqrstuvwxyz123",
    )
    with app.app_context():
        diag = svc.diagnostics()

    assert diag["cloud_name"] == {"present": True, "length": 8}
    assert diag["api_key"] == {"present": True, "length": 15}
    assert diag["configured"] is True

    text = str(diag)
    assert "123456789012345" not in text
    assert "abcdefghijklmnopqrstuvwxyz123" not in text


def test_diagnostics_missing_credentials():
    app = _make_app()
    with app.app_context():
        diag = svc.diagnostics()
    assert diag["configured"] is False
    assert diag["cloud_name"]["present"] is False
    assert diag["api_key"]["present"] is False
    assert diag["api_secret"]["present"] is False


def test_verify_credentials_missing():
    app = _make_app()
    with app.app_context():
        ok, detail = svc.verify_credentials()
    assert ok is False
    assert detail == "missing_configuration"


def test_verify_credentials_authorization_failure(monkeypatch):
    app = _make_app(cloud_name="c", api_key="k", api_secret="s")
    monkeypatch.setattr("cloudinary.api.ping", _raise_auth)
    with app.app_context():
        ok, detail = svc.verify_credentials()
    assert ok is False
    assert detail == "authorization_required"


def test_verify_credentials_success(monkeypatch):
    app = _make_app(cloud_name="c", api_key="k", api_secret="s")
    monkeypatch.setattr("cloudinary.api.ping", lambda **kw: {"status": "ok"})
    with app.app_context():
        ok, detail = svc.verify_credentials()
    assert ok is True
    assert detail == "ok"


def test_upload_raises_auth_error_on_authorization_required(monkeypatch):
    import io

    app = _make_app(cloud_name="c", api_key="k", api_secret="s")
    monkeypatch.setattr("cloudinary.uploader.upload", _raise_auth)
    with app.app_context():
        try:
            svc.upload_image(io.BytesIO(b"x"))
        except svc.CloudinaryAuthError:
            return
        except svc.CloudinaryUploadError:
            pass
    raise AssertionError("expected CloudinaryAuthError")
