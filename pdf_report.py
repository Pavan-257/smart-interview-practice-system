from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import darkblue
from bs4 import BeautifulSoup


def generate_pdf(
    filename,
    name,
    interview_type,
    score,
    feedback
):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    title = styles["Title"]
    title.alignment = TA_CENTER
    title.textColor = darkblue

    heading = styles["Heading2"]

    normal = styles["BodyText"]

    elements = []

    elements.append(
        Paragraph(
            "SMART INTERVIEW PRACTICE SYSTEM",
            title
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"<b>Candidate Name:</b> {name}", heading))
    elements.append(Paragraph(f"<b>Interview Type:</b> {interview_type}", heading))

    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"<b>Overall Score:</b> {score}", heading))

    try:
        numeric_score = int(str(score).replace("%", "").strip())
    except:
        numeric_score = 0

    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>AI Feedback</b>", heading))
    soup = BeautifulSoup(feedback, "html.parser")

    clean_feedback = soup.get_text()

    elements.append(Paragraph(clean_feedback.replace("\n", "<br/>"), normal))

    elements.append(Spacer(1, 20))

    if numeric_score >= 90:
        result = "Excellent Performance"

    elif numeric_score >= 75:
          result = "Very Good"

    elif numeric_score >= 60:
          result = "Good"

    elif numeric_score >= 40:
          result = "Needs Improvement"

    else:
        result = "Poor Performance"

    elements.append(Paragraph(f"<b>Final Result:</b> {result}", heading))

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "Generated automatically by Smart Interview Practice System.",
            normal
        )
    )

    doc.build(elements)