import jinja2
import weasyprint

def render_pdf(data) -> bytes:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("app/reports/templates")
    )
    template = env.get_template("report.html")
    html_string = template.render(data=data)
    pdf_bytes = weasyprint.HTML(string=html_string).write_pdf()
    return pdf_bytes
