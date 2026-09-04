import io
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from PIL import Image as PILImage, ImageDraw

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
    HRFlowable
)

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger("services.report.generator")

class ReportGenerator:
    """
    Generates official, high-fidelity PDF inspection reports
    with strict separation of DETECTED FACT, RULE REQUIREMENT, and SYSTEM FINDING.
    """

    @classmethod
    def generate_pdf(
        cls,
        dossier: Dict[str, Any],
        image_path: Optional[str] = None
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0F172A'),
            alignment=0,
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#2563EB'),
            textTransform='uppercase',
            spaceAfter=4
        )
        meta_label = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#64748B')
        )
        meta_val = ParagraphStyle(
            'MetaVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0F172A')
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=12,
            spaceAfter=6
        )
        table_cell = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1E293B')
        )
        table_cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#0F172A')
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#475569')
        )

        story = []

        # 1. Official Header
        story.append(Paragraph("DIRECTORATE OF LEGAL METROLOGY", subtitle_style))
        story.append(Paragraph("PRELIMINARY STATUTORY COMPLIANCE SCREENING REPORT", title_style))
        story.append(Paragraph("Issued under Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011", ParagraphStyle('SubSub', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#475569'), spaceAfter=8)))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=10))

        # 2. Metadata Grid
        insp_id = dossier.get("inspection_id", "N/A")
        created_at = dossier.get("created_at", datetime.now(timezone.utc).isoformat())
        inspector = dossier.get("inspector", {})
        product = dossier.get("product", {})
        compliance = dossier.get("compliance_result", {})
        overall_status = dossier.get("overall_status", "NOT_EVALUATED")
        risk_score = dossier.get("risk_score", 0)
        rule_version = dossier.get("rule_version", "2026.1")
        review_status = dossier.get("review_status", "PENDING")

        status_color = colors.HexColor('#16A34A') if overall_status == "COMPLIANT" else (colors.HexColor('#DC2626') if overall_status == "POTENTIAL_VIOLATION" else colors.HexColor('#D97706'))

        meta_data = [
            [
                Paragraph("<b>Inspection ID:</b>", meta_label),
                Paragraph(f"<font color='#2563EB'><b>{insp_id}</b></font>", meta_val),
                Paragraph("<b>Date & Time:</b>", meta_label),
                Paragraph(str(created_at).replace("T", " ")[:19] + " UTC", meta_val)
            ],
            [
                Paragraph("<b>Inspector:</b>", meta_label),
                Paragraph(f"{inspector.get('full_name', 'Inspector General')} ({inspector.get('username', 'inspector_lm')})", meta_val),
                Paragraph("<b>Review Status:</b>", meta_label),
                Paragraph(f"<b>{review_status}</b>", meta_val)
            ],
            [
                Paragraph("<b>Product / Commodity:</b>", meta_label),
                Paragraph(product.get("product_name") or product.get("name") or "Packaged Commodity", meta_val),
                Paragraph("<b>Manufacturer:</b>", meta_label),
                Paragraph(product.get("manufacturer") or "Not Declared", meta_val)
            ],
            [
                Paragraph("<b>Rule Catalog:</b>", meta_label),
                Paragraph(f"Version {rule_version}", meta_val),
                Paragraph("<b>Preliminary Finding:</b>", meta_label),
                Paragraph(f"<b>{overall_status} (Risk: {risk_score}/100)</b>", ParagraphStyle('St', parent=meta_val, textColor=status_color, fontName='Helvetica-Bold'))
            ]
        ]

        meta_table = Table(meta_data, colWidths=[110, 160, 110, 160])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # 3. Product Photograph & Evidence Region (Annotated)
        if image_path and os.path.exists(image_path):
            try:
                # Open original image, resize thumbnail for PDF
                pil_img = PILImage.open(image_path)
                # If RGB draw boxes for evidence
                draw_img = pil_img.convert("RGB")
                draw = ImageDraw.Draw(draw_img)
                w_orig, h_orig = pil_img.size

                evidence_items = dossier.get("evidence", [])
                for ev in evidence_items:
                    box = ev.get("bounding_box")
                    if box and isinstance(box, dict):
                        bx = box.get("x", 0)
                        by = box.get("y", 0)
                        bw = box.get("width", 0)
                        bh = box.get("height", 0)
                        outline_color = (220, 38, 38) if ev.get("type") == "INCORRECT_DECLARATION" else (37, 99, 235)
                        draw.rectangle([bx, by, bx + bw, by + bh], outline=outline_color, width=4)

                thumb_buf = io.BytesIO()
                # Maintain aspect ratio to fit 240 width, max 160 height
                draw_img.thumbnail((260, 180))
                draw_img.save(thumb_buf, format="JPEG")
                thumb_buf.seek(0)

                img_flow = RLImage(thumb_buf, width=200, height=140)

                img_meta = [
                    [
                        img_flow,
                        Paragraph(
                            "<b>SPATIAL EVIDENCE GROUNDING OVERLAY</b><br/><br/>"
                            "The adjacent photograph represents the ingested packaging asset. "
                            "Grounded bounding boxes indicate physical label declarations localized by the computer vision perception layer.<br/><br/>"
                            "• <b>Red Boxes:</b> Statutory non-compliance / format defects.<br/>"
                            "• <b>Blue Boxes:</b> Verified compliant declarations.<br/>"
                            "• <b>Absence Notices:</b> Mandatory declarations verified missing from label.",
                            table_cell
                        )
                    ]
                ]
                img_table = Table(img_meta, colWidths=[210, 330])
                img_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                    ('PADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(img_table)
                story.append(Spacer(1, 10))
            except Exception as e:
                logger.warning(f"Could not embed packaging image in PDF: {e}")

        # 4. Core Declarations & Compliance Ledger
        # Must clearly distinguish: DETECTED FACT vs RULE REQUIREMENT vs SYSTEM FINDING
        story.append(Paragraph("MANDATORY STATUTORY DECLARATION AUDIT LEDGER", section_heading))
        story.append(Paragraph(
            "The table below strictly differentiates between <b>[DETECTED FACT]</b> (grounded label perception), "
            "<b>[RULE REQUIREMENT]</b> (statutory mandate), and <b>[SYSTEM FINDING]</b> (compliance verdict).",
            disclaimer_style
        ))
        story.append(Spacer(1, 6))

        headers = [
            Paragraph("<b>FIELD / RULE</b>", table_cell_bold),
            Paragraph("<b>DETECTED FACT<br/>(AI / OCR Perception)</b>", table_cell_bold),
            Paragraph("<b>RULE REQUIREMENT<br/>(PCR 2011 Mandate)</b>", table_cell_bold),
            Paragraph("<b>SYSTEM FINDING<br/>(Preliminary Signal)</b>", table_cell_bold)
        ]

        table_rows = [headers]

        checks = compliance.get("checks", [])
        for chk in checks:
            rule_id = chk.get("rule_id", "LM-???")
            field = chk.get("field", "").replace("_", " ").upper()
            val = chk.get("extracted_value")
            conf = Math_conf = float(chk.get("confidence", 0.0))
            status = chk.get("status", "N/A")
            req = chk.get("requirement") or "Mandatory legal declaration under Packaged Commodities Rules, 2011."
            reason = chk.get("reason", "")

            # Detected Fact column
            if val is not None and str(val).strip() != "":
                detected_p = Paragraph(f"<b>Value:</b> \"{val}\"<br/><b>Confidence:</b> {int(conf * 100)}%", table_cell)
            else:
                detected_p = Paragraph("<font color='#D97706'><i>null (Not Found)</i></font><br/><b>Confidence:</b> 0%", table_cell)

            # Rule Requirement column
            req_p = Paragraph(f"<b>[{rule_id}]</b><br/>{req}", table_cell)

            # System Finding column
            if status == "COMPLIANT":
                st_badge = "<font color='#16A34A'><b>✓ COMPLIANT</b></font>"
            elif status == "POTENTIAL_VIOLATION":
                st_badge = "<font color='#DC2626'><b>❌ POTENTIAL VIOLATION</b></font>"
            elif status == "MANUAL_REVIEW":
                st_badge = "<font color='#D97706'><b>⚠ MANUAL REVIEW</b></font>"
            else:
                st_badge = "<font color='#64748B'><b>NOT APPLICABLE</b></font>"

            finding_p = Paragraph(f"{st_badge}<br/>{reason}", table_cell)

            table_rows.append([
                Paragraph(f"<b>{field}</b><br/><font color='#64748B'>{rule_id}</font>", table_cell_bold),
                detected_p,
                req_p,
                finding_p
            ])

        col_widths = [85, 125, 170, 160]
        audit_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
        audit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#94A3B8')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(audit_table)
        story.append(Spacer(1, 12))

        # 5. Statutory Disclaimer (Non-binding AI signal)
        disclaimer_box = [
            [
                Paragraph(
                    "<b>LEGAL NOTICE & STATUTORY DISCLAIMER:</b><br/>"
                    "This document is an AI-assisted preliminary compliance screening report generated to aid Legal Metrology "
                    "enforcement officers. Findings, confidence scores, and detection outputs contained herein are preliminary technical signals "
                    "and <b>DO NOT constitute legally binding adjudications, penalty orders, or compounded offence notices</b>. "
                    "Final regulatory determinations remain exclusively within the jurisdiction of authorized Legal Metrology inspectors "
                    "subject to mandatory manual inspection and verification under the Legal Metrology Act, 2009.",
                    disclaimer_style
                )
            ]
        ]
        disclaimer_table = Table(disclaimer_box, colWidths=[540])
        disclaimer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F59E0B')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        # 5b. Human Inspector Determination & Sign-off Block
        review_data = dossier.get("review", {}) or {}
        decision_val = review_data.get("decision", "PENDING REVIEW")
        reviewer_id = review_data.get("reviewer_id", "Inspector of Legal Metrology")
        review_notes = review_data.get("notes", "Preliminary AI screening awaiting inspector sign-off.")
        review_ts = review_data.get("reviewed_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

        signoff_meta = [
            [
                Paragraph(
                    f"<b>OFFICIAL HUMAN DETERMINATION & STATUTORY SIGN-OFF</b><br/><br/>"
                    f"<b>Inspector Decision:</b> {decision_val}<br/>"
                    f"<b>Reviewing Officer:</b> {reviewer_id}<br/>"
                    f"<b>Review Timestamp:</b> {review_ts}<br/>"
                    f"<b>Inspector Remarks:</b> {review_notes}",
                    table_cell
                ),
                Paragraph(
                    "<br/><br/><br/>"
                    "____________________________________________<br/>"
                    "<b>Authorized Inspector of Legal Metrology</b><br/>"
                    "Controllerate of Legal Metrology<br/>"
                    "Department of Consumer Affairs, Govt. of India",
                    table_cell_bold
                )
            ]
        ]
        signoff_table = Table(signoff_meta, colWidths=[310, 230])
        signoff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#0F172A')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(Spacer(1, 10))
        story.append(KeepTogether(signoff_table))
        story.append(Spacer(1, 10))

        story.append(KeepTogether(disclaimer_table))

        # Build document
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
