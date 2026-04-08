"""app/reports/renderer.py — Render the clinical PDF report using Jinja2 + WeasyPrint."""
import os
import jinja2
import weasyprint

# Resolve template directory relative to this file's location so the loader
# works regardless of the process working directory.
_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def render_pdf(data) -> bytes:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(_TEMPLATE_DIR),
        autoescape=True,
    )
    template = env.get_template("report.html")
    html_string = template.render(data=data)
    base_url = f"file://{_TEMPLATE_DIR}/"
    pdf_bytes = weasyprint.HTML(string=html_string, base_url=base_url).write_pdf()
    if pdf_bytes is None:
        raise RuntimeError("Failed to render PDF")
    return pdf_bytes
