from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, HRFlowable
)


def create_summary_pdf(result: dict, source_name: str = "NotePilot AI") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="NotePilot AI Summary",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="NPTitle", parent=styles["Title"], textColor=colors.HexColor("#6245A5"),
        alignment=TA_CENTER, fontSize=22, leading=27, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="NPHeading", parent=styles["Heading2"], textColor=colors.HexColor("#6245A5"),
        fontSize=14, leading=18, spaceBefore=12, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="NPBody", parent=styles["BodyText"], fontSize=9.5, leading=14,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="NPSub", parent=styles["BodyText"], textColor=colors.HexColor("#77718A"),
        fontSize=8.5, leading=12, alignment=TA_CENTER
    ))

    story = [
        Paragraph("NotePilot AI", styles["NPTitle"]),
        Paragraph("Intelligent Lecture Summarization &amp; Action Item Extraction", styles["NPSub"]),
        Spacer(1, 5 * mm),
        Paragraph(escape(str(result.get("title", "Summary"))), styles["Heading1"]),
        Paragraph(f"Source: {escape(str(source_name))}", styles["NPSub"]),
        HRFlowable(width="100%", color=colors.HexColor("#DED5F5"), thickness=1),
        Paragraph("1. Summary", styles["NPHeading"]),
        Paragraph(escape(str(result.get("summary", "No summary available."))), styles["NPBody"]),
    ]

    def add_bullets(items, formatter=str):
        if not items:
            story.append(Paragraph("No items available.", styles["NPBody"]))
            return
        flow_items = []
        for item in items:
            flow_items.append(ListItem(Paragraph(formatter(item), styles["NPBody"])))
        story.append(ListFlowable(flow_items, bulletType="bullet", leftIndent=14))

    story.append(Paragraph("2. Key Points", styles["NPHeading"]))
    add_bullets(result.get("key_points", []), lambda x: escape(str(x)))

    story.append(Paragraph("3. Important Concepts", styles["NPHeading"]))
    concepts = result.get("important_concepts", [])
    if concepts:
        for concept in concepts:
            if isinstance(concept, dict):
                term = escape(str(concept.get("term", "Concept")))
                explanation = escape(str(concept.get("explanation", "")))
                story.append(Paragraph(f"<b>{term}:</b> {explanation}", styles["NPBody"]))
    else:
        story.append(Paragraph("No concepts available.", styles["NPBody"]))

    story.append(Paragraph("4. Next Action Items", styles["NPHeading"]))
    actions = result.get("action_items", [])
    if actions:
        for action in actions:
            if isinstance(action, dict):
                task = escape(str(action.get("task", "")))
                priority = escape(str(action.get("priority", "Not specified")))
                deadline = escape(str(action.get("deadline", "Not specified")))
                basis = escape(str(action.get("basis", "")))
                story.append(Paragraph(
                    f"<b>{task}</b><br/>Priority: {priority} | Deadline: {deadline}<br/>{basis}",
                    styles["NPBody"]
                ))
    else:
        story.append(Paragraph("No action items available.", styles["NPBody"]))

    story.append(Paragraph("5. Learning Roadmap", styles["NPHeading"]))
    roadmap = result.get("roadmap", [])
    if roadmap:
        for index, step in enumerate(roadmap, start=1):
            if isinstance(step, dict):
                title = escape(str(step.get("title", f"Step {index}")))
                description = escape(str(step.get("description", "")))
                duration = escape(str(step.get("estimated_time", "Not specified")))
                story.append(Paragraph(
                    f"<b>{index}. {title}</b><br/>{description}<br/>Estimated time: {duration}",
                    styles["NPBody"]
                ))
    else:
        story.append(Paragraph("No roadmap available.", styles["NPBody"]))

    story.append(Paragraph("6. Revision Questions", styles["NPHeading"]))
    add_bullets(result.get("study_questions", []), lambda x: escape(str(x)))

    doc.build(story)
    return buffer.getvalue()
