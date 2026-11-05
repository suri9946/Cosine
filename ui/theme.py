"""COSIN UI Theme and Design System.

Light-themed, clean, scientific design specifications.
Colors, typography, badges, and layout utilities.
"""

# Palette definitions
BG_MAIN = "#F8F9FA"         # Warm off-white
SURFACE_WHITE = "#FFFFFF"   # Pure white
TEXT_PRIMARY = "#1A202C"    # Dark charcoal
TEXT_SECONDARY = "#5A6A80"  # Muted grey
BORDER_LIGHT = "#E2E8F0"    # Soft light grey
ACCENT_TEAL = "#14746F"     # Muted scientific teal
ACCENT_HOVER = "#0E5B57"
ACCENT_SUBTLE = "#E6F4F1"

# Status colors
STATUS_COLORS = {
    "APPROVED": {"bg": "#E6F4EA", "border": "#A8DAB5", "text": "#137333", "label": "Approved"},
    "APPROVED_WITH_LIMITATIONS": {"bg": "#FEF7E0", "border": "#FAD97C", "text": "#B06000", "label": "Approved with Limitations"},
    "NEEDS_MORE_EVIDENCE": {"bg": "#FEF7E0", "border": "#FAD97C", "text": "#B06000", "label": "Needs More Evidence"},
    "ABSTAIN": {"bg": "#F1F3F4", "border": "#DADCE0", "text": "#5F6368", "label": "Abstain"},
    "PARTIAL": {"bg": "#FEF7E0", "border": "#FAD97C", "text": "#B06000", "label": "Partial Evidence"},
    "REJECTED": {"bg": "#FCE8E6", "border": "#F5A8A0", "text": "#C5221F", "label": "Rejected"},
    "FAILED": {"bg": "#FCE8E6", "border": "#F5A8A0", "text": "#C5221F", "label": "Stage Failed"},
    "RUNNING": {"bg": "#E8F0FE", "border": "#AECBFA", "text": "#1967D2", "label": "Running"},
    "WAITING": {"bg": "#F8F9FA", "border": "#E2E8F0", "text": "#718096", "label": "Waiting"},
    "COMPLETED": {"bg": "#E6F4EA", "border": "#A8DAB5", "text": "#137333", "label": "Completed"},
    "NEEDS_ATTENTION": {"bg": "#FEF7E0", "border": "#FAD97C", "text": "#B06000", "label": "Needs Attention"},
}

CUSTOM_CSS = """
<style>
/* Base typography — do not target [class*="st-"] to prevent breaking Streamlit Material icon fonts */
html, body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1A202C;
    background-color: #F8F9FA;
}

.stApp {
    background-color: #F8F9FA;
}

/* Ensure Material symbols and icon fonts are NEVER overridden */
.material-symbols-rounded,
.material-icons,
[data-testid*="Icon"],
[data-testid="stIconMaterial"],
i.material-symbols-rounded {
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    font-style: normal;
    text-transform: none;
    letter-spacing: normal;
    word-wrap: normal;
    white-space: nowrap;
    direction: ltr;
}

/* Clean Sidebar */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
    box-shadow: none;
}

/* Primary buttons (Submit Research) */
button[kind="primary"] {
    background-color: #14746F !important;
    border: 1px solid #0E5B57 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    border-radius: 6px !important;
    padding: 0.55rem 1.5rem !important;
    transition: all 0.15s ease-in-out !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

button[kind="primary"]:hover {
    background-color: #0E5B57 !important;
    border-color: #093E3B !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
}

/* Secondary buttons */
button[kind="secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E0 !important;
    color: #2D3748 !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    padding: 0.4rem 0.85rem !important;
    text-align: left !important;
}

button[kind="secondary"]:hover {
    background-color: #F7FAFC !important;
    border-color: #14746F !important;
    color: #14746F !important;
}

/* Cards and surfaces */
.cosin-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.cosin-card-highlight {
    background-color: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}

.cosin-plain-summary {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 5px solid #14746F;
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.cosin-fact-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
}

.cosin-fact-item {
    background-color: #F8F9FA;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 0.75rem 1rem;
}

.cosin-fact-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    font-weight: 600;
    color: #5A6A80;
    letter-spacing: 0.03em;
}

.cosin-fact-val {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1A202C;
    margin-top: 0.2rem;
}

/* Status badges */
.status-pill {
    display: inline-flex;
    align-items: center;
    font-size: 0.8125rem;
    font-weight: 600;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    border: 1px solid transparent;
    letter-spacing: 0.02em;
}

/* Brand header */
.cosin-brand {
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #14746F;
    margin: 0;
    padding: 0;
}

.cosin-subtitle {
    font-size: 0.875rem;
    color: #5A6A80;
    margin-top: 0.15rem;
    margin-bottom: 1rem;
}

/* Citations tag */
.citation-tag {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.75rem;
    background-color: #EDF2F7;
    color: #2D3748;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    border: 1px solid #CBD5E0;
    margin-right: 0.35rem;
}

/* Stage card */
.stage-box {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
    transition: all 0.2s ease;
}

.stage-box.running {
    border-left: 4px solid #1967D2;
    background-color: #FAFCFF;
}

.stage-box.completed {
    border-left: 4px solid #137333;
}

.stage-box.needs_attention {
    border-left: 4px solid #B06000;
}

.stage-box.failed {
    border-left: 4px solid #C5221F;
}

.stage-box.waiting {
    border-left: 4px solid #CBD5E0;
    opacity: 0.85;
}
</style>
"""


def render_status_pill(status: str, label_override: str | None = None) -> str:
    """Generate HTML for a refined scientific status badge."""
    cfg = STATUS_COLORS.get(status, STATUS_COLORS["WAITING"])
    text = label_override or cfg["label"]
    return (
        f'<span class="status-pill" style="background-color: {cfg["bg"]}; '
        f'border-color: {cfg["border"]}; color: {cfg["text"]};">'
        f'{text}</span>'
    )
