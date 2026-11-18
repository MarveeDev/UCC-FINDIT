from datetime import date, time

from app.items.models import ITEM_CATEGORIES, ReportType


def _parse_date(value):
    try:
        return date.fromisoformat(str(value).strip())
    except (ValueError, TypeError):
        return None


def _parse_time(value):
    try:
        return time.fromisoformat(str(value).strip())
    except (ValueError, TypeError):
        return None


def validate_report(data):
    """Validate raw report input, returning (errors, cleaned).

    Existence checks (location validity) are handled by the service layer so
    they can raise typed 400 responses rather than field-level errors.
    """
    errors = {}

    report_type = (data.get("report_type") or "").strip().upper()
    item_name = (data.get("item_name") or "").strip()
    category = (data.get("category") or "").strip()
    description = (data.get("description") or "").strip()
    brand = (data.get("brand") or "").strip() or None
    colour = (data.get("colour") or "").strip() or None
    identifying = (data.get("identifying_characteristics") or "").strip() or None
    custody = (data.get("custody_info") or "").strip() or None
    image_path = (data.get("image_path") or "").strip() or None
    location_id = data.get("location_id")
    event_date_raw = data.get("event_date")
    event_time_raw = data.get("event_time")

    if report_type not in ReportType.ALL:
        errors["report_type"] = "report_type must be LOST or FOUND"

    if not item_name:
        errors["item_name"] = "Item name is required"
    elif len(item_name) > 120:
        errors["item_name"] = "Item name is too long"

    if not category:
        errors["category"] = "Category is required"
    elif category not in ITEM_CATEGORIES:
        errors["category"] = "Category is invalid"

    if not description:
        errors["description"] = "Description is required"
    elif len(description) > 2000:
        errors["description"] = "Description is too long"

    if brand and len(brand) > 80:
        errors["brand"] = "Brand is too long"
    if colour and len(colour) > 40:
        errors["colour"] = "Colour is too long"
    if identifying and len(identifying) > 1000:
        errors["identifying_characteristics"] = "Identifying characteristics are too long"

    event_date = _parse_date(event_date_raw)
    if not event_date_raw:
        errors["event_date"] = "Event date is required"
    elif event_date is None:
        errors["event_date"] = "Event date must be a valid date (YYYY-MM-DD)"
    elif event_date > date.today():
        errors["event_date"] = "Event date cannot be in the future"

    event_time = None
    if event_time_raw:
        event_time = _parse_time(event_time_raw)
        if event_time is None:
            errors["event_time"] = "Event time must be a valid time (HH:MM)"

    if location_id is None:
        errors["location_id"] = "Location is required"

    cleaned = {
        "report_type": report_type,
        "item_name": item_name,
        "category": category,
        "description": description,
        "brand": brand,
        "colour": colour,
        "identifying_characteristics": identifying,
        "custody_info": custody,
        "image_path": image_path,
        "location_id": location_id,
        "event_date": event_date,
        "event_time": event_time,
    }
    return errors, cleaned
