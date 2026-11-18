"""Item matching engine.

This module is the extension point for rule-based lost/found matching, planned
for a later milestone. The evaluation function is intentionally a no-op that
returns no candidates for now so the report-creation flow can call it without
introducing dead code later.
"""


def evaluate_report(report):
    """Return candidate match records for a newly created report.

    Future implementation: compare category, item name, brand, colour,
    description keywords, location and date proximity between lost and found
    reports, returning transparent rule-based scores with reasons.
    """
    return []
