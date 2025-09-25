# Global, multilingual FAQ/document categories configuration
# Each category has a stable string `key` used in code/DB, with
# translatable `label` and `description`.

# Provide a translation function `_` if the application hasn't configured
# gettext or a translation lookup. This mirrors common Django/Flask patterns
# where `_` is globally available; here we fall back to identity to keep
# the module importable in minimal environments and tests.
try:
    from gettext import gettext as _  # type: ignore
except Exception:  # pragma: no cover - fallback safety
    def _(s: str) -> str:  # type: ignore
        return s

DOC_CATEGORIES = [
    {
        "key": "business_company_overview",
        "label": _("Business - Company Overview"),
        "description": _("Company profile, history, mission, vision, and organizational structure."),
        "icon": "business",
        "area": "OPERATIONS",
        "relationship": "both",
    },
    {
        "key": "business_financial_reports",
        "label": _("Business - Financial Reports"),
        "description": _("Annual reports, financial statements, balance sheets, and audit reports."),
        "icon": "bar_chart",
        "area": "FINANCE",
        "relationship": "both",
    },
    {
        "key": "business_certifications_awards",
        "label": _("Business - Certifications & Awards"),
        "description": _("Industry certifications, awards, recognitions, audit reports, and compliance documents."),
        "icon": "verified",
        "area": "MARKETING",
        "relationship": "both",
    },
    {
        "key": "sales_product_portfolio",
        "label": _("Sales - Product Portfolio"),
        "description": _("Product/service descriptions, technical specifications, and pricing sheets."),
        "icon": "inventory",
        "area": "SALES",
        "relationship": "both",
    },
    {
        "key": "sales_customer_references",
        "label": _("Sales - Customer References"),
        "description": _("Customer lists, reference letters, testimonials, and case studies."),
        "icon": "groups",
        "area": "MARKETING",
        "relationship": "client",
    },
    {
        "key": "sales_rfx",
        "label": _("Sales - RFx Received"),
        "description": _("RFP/RFI/RFQ received that need to be answered."),
        "icon": "assignment",
        "area": "SALES",
        "relationship": "supplier",
    },
    {
        "key": "marketing_business_cases",
        "label": _("Marketing - Business Cases"),
        "description": _("Business cases, ROI analyses, and value proposition documents."),
        "icon": "lightbulb",
        "area": "MARKETING",
        "relationship": "both",
    },
    {
        "key": "marketing_customer_success_stories",
        "label": _("Marketing - Customer Success Stories"),
        "description": _("Customer user cases, success stories, and project outcomes."),
        "icon": "emoji_events",
        "area": "MARKETING",
        "relationship": "client",
    },
    {
        "key": "marketing_white_papers_innovation",
        "label": _("Marketing - White Papers & Innovation"),
        "description": _("White papers, innovation reports, and thought leadership materials."),
        "icon": "science",
        "area": "MARKETING",
        "relationship": "both",
    },
    {
        "key": "marketing_brochures_presentations",
        "label": _("Marketing - Brochures & Presentations"),
        "description": _("Brochures, presentations, and promotional materials."),
        "icon": "campaign",
        "area": "MARKETING",
        "relationship": "both",
    },
]

# Fast lookup by key
DOC_CATEGORIES_BY_KEY = {c["key"]: c for c in DOC_CATEGORIES}

# Choices helpers for forms/admin
DOC_CATEGORY_CHOICES = [(c["key"], c["label"]) for c in DOC_CATEGORIES]

