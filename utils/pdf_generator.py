from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def generate_pdf(prescription):
    """Generate in memory; never leave unencrypted exports on disk."""
    output = BytesIO()
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#17665c")
    story = [Paragraph("MedRec | Care summary", styles["Title"]), Spacer(1, 20)]
    fields = [
        ("Record", str(prescription.id)),
        ("Date", prescription.date_issued.strftime("%Y-%m-%d")),
        ("Assessment", prescription.disease),
        ("Care notes", prescription.description),
    ]
    for label, value in fields:
        story.extend(
            [
                Paragraph(label, styles["Heading2"]),
                Paragraph(escape(value).replace(chr(10), "<br/>"), styles["BodyText"]),
                Spacer(1, 12),
            ]
        )
    story.append(
        Paragraph("Educational portfolio demonstration. Not a clinical prescription.", styles["Italic"])
    )
    SimpleDocTemplate(output, title="MedRec care summary").build(story)
    output.seek(0)
    return output
