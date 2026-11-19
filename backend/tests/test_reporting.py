import pytest

from app.reporting import services as reporting_services


def _fail_create(reporter, data):
    raise RuntimeError("simulated DB persistence failure")


def test_submit_report_deletes_image_on_persistence_failure(monkeypatch):
    calls = []

    def _record_delete(public_id):
        calls.append(public_id)
        return True

    monkeypatch.setattr("app.items.services.create_report", _fail_create)
    monkeypatch.setattr("app.reporting.services.delete_image", _record_delete)

    with pytest.raises(RuntimeError):
        reporting_services.submit_report(
            reporter=None, cleaned={"image_public_id": "ucc-findit/items/abc123"}
        )

    assert calls == ["ucc-findit/items/abc123"]


def test_submit_report_does_not_delete_when_no_image(monkeypatch):
    calls = []

    def _record_delete(public_id):
        calls.append(public_id)
        return True

    monkeypatch.setattr("app.items.services.create_report", _fail_create)
    monkeypatch.setattr("app.reporting.services.delete_image", _record_delete)

    with pytest.raises(RuntimeError):
        reporting_services.submit_report(reporter=None, cleaned={})

    assert calls == []
