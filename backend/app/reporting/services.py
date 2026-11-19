"""Report submission orchestration.

Centralises the post-creation side effects (manager notification, match
evaluation, match notifications) so every report entry point — the standard
report endpoint and the QR recovery flow — follows the same sequence without
duplicating logic or creating import cycles.
"""

from app.items import services as item_services
from app.matching import services as matching_services
from app.notifications import services as notification_services
from app.uploads.cloudinary_service import delete_image


def submit_report(reporter, cleaned):
    try:
        report = item_services.create_report(reporter, cleaned)
    except Exception:
        # Roll back any newly uploaded image if the report could not be
        # persisted, so we don't leave an orphaned Cloudinary asset behind.
        public_id = cleaned.get("image_public_id")
        if public_id:
            delete_image(public_id)
        raise
    run_side_effects(report)
    return report


def run_side_effects(report):
    """Run post-commit side effects for a newly created report."""
    notification_services.notify_location_managers(report)
    matches = matching_services.evaluate_report(report)
    notification_services.notify_possible_matches(matches)
