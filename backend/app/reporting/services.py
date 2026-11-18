"""Report submission orchestration.

Centralises the post-creation side effects (manager notification, match
evaluation, match notifications) so every report entry point — the standard
report endpoint and the QR recovery flow — follows the same sequence without
duplicating logic or creating import cycles.
"""

from app.items import services as item_services
from app.matching import services as matching_services
from app.notifications import services as notification_services


def submit_report(reporter, cleaned):
    report = item_services.create_report(reporter, cleaned)
    notification_services.notify_location_managers(report)
    matches = matching_services.evaluate_report(report)
    notification_services.notify_possible_matches(matches)
    return report
