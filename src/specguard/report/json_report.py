from specguard.models.entities import ReviewReport


def render_json(report: ReviewReport) -> dict:
    return report.model_dump(mode="json")
