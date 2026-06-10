from datetime import datetime, timedelta
from io import BytesIO
from bson import ObjectId
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from ..database import get_database


class ReportService:
    @staticmethod
    def _register_fonts():
        try:
            pdfmetrics.registerFont(TTFont("STSong", "/System/Library/Fonts/Supplemental/Songti.ttc"))
            return "STSong"
        except Exception:
            try:
                pdfmetrics.registerFont(
                    TTFont("Helvetica", "/Library/Fonts/Arial.ttf")
                )
                return "Helvetica"
            except Exception:
                return "Helvetica"

    @classmethod
    async def generate_report(cls, monitor_id: ObjectId) -> bytes:
        db = get_database()
        font_name = cls._register_fonts()

        monitor = await db.monitors.find_one({"_id": monitor_id})
        if not monitor:
            raise ValueError("Monitor not found")

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=24,
            leading=30,
            alignment=1,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=20,
        )
        h1_style = ParagraphStyle(
            "H1",
            parent=styles["Heading1"],
            fontName=font_name,
            fontSize=16,
            leading=22,
            textColor=colors.HexColor("#16213e"),
            spaceAfter=12,
            spaceBefore=16,
        )
        h2_style = ParagraphStyle(
            "H2",
            parent=styles["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#0f3460"),
            spaceAfter=8,
            spaceBefore=10,
        )
        normal_style = ParagraphStyle(
            "NormalCN",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=16,
            textColor=colors.black,
        )

        elements = []

        elements.append(Paragraph("舆情监控分析报告", title_style))
        elements.append(HRFlowable(
            width="100%", thickness=2, color=colors.HexColor("#e94560"),
            spaceBefore=0, spaceAfter=20,
        ))

        elements.append(Paragraph("一、监控任务概览", h1_style))
        info_data = [
            ["任务名称", monitor.get("name", "")],
            ["关键词", ", ".join(monitor.get("keywords", []))],
            ["监控来源", ", ".join(monitor.get("sources", []))],
            ["情感阈值", str(monitor.get("sentiment_threshold", -0.3))],
            ["创建时间", str(monitor.get("created_at", ""))],
            ["报告生成时间", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")],
        ]
        info_table = Table(info_data, colWidths=[4 * cm, 11 * cm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e2ec")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(info_table)

        now = datetime.utcnow()
        start_time = now - timedelta(days=7)

        total_count = await db.collected_data.count_documents({
            "monitor_id": monitor_id,
            "collected_at": {"$gte": start_time},
        })
        positive_count = await db.collected_data.count_documents({
            "monitor_id": monitor_id,
            "sentiment_label": "positive",
            "collected_at": {"$gte": start_time},
        })
        negative_count = await db.collected_data.count_documents({
            "monitor_id": monitor_id,
            "sentiment_label": "negative",
            "collected_at": {"$gte": start_time},
        })
        neutral_count = await db.collected_data.count_documents({
            "monitor_id": monitor_id,
            "sentiment_label": "neutral",
            "collected_at": {"$gte": start_time},
        })

        avg_sentiment = 0
        if total_count > 0:
            sentiment_cursor = db.collected_data.aggregate([
                {"$match": {"monitor_id": monitor_id, "collected_at": {"$gte": start_time}}},
                {"$group": {"_id": None, "avg": {"$avg": "$sentiment_score"}}},
            ])
            sentiment_result = await sentiment_cursor.to_list(length=1)
            if sentiment_result:
                avg_sentiment = round(sentiment_result[0]["avg"], 4)

        elements.append(Paragraph("二、数据统计（近7天）", h1_style))
        stat_data = [
            ["指标", "数值"],
            ["总采集数据量", str(total_count)],
            ["正面舆情数", str(positive_count)],
            ["负面舆情数", str(negative_count)],
            ["中性舆情数", str(neutral_count)],
            ["平均情感得分", str(avg_sentiment)],
            ["正面占比", f"{round(positive_count / total_count * 100, 2) if total_count else 0}%"],
            ["负面占比", f"{round(negative_count / total_count * 100, 2) if total_count else 0}%"],
        ]
        stat_table = Table(stat_data, colWidths=[6 * cm, 9 * cm])
        stat_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e2ec")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(stat_table)

        elements.append(PageBreak())

        elements.append(Paragraph("三、来源分布统计", h1_style))
        source_pipeline = [
            {"$match": {"monitor_id": monitor_id, "collected_at": {"$gte": start_time}}},
            {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
        ]
        source_results = await db.collected_data.aggregate(source_pipeline).to_list(length=None)
        source_data = [["来源类型", "数量", "占比"]]
        for sr in source_results:
            source_data.append([
                sr["_id"],
                str(sr["count"]),
                f"{round(sr['count'] / total_count * 100, 2) if total_count else 0}%",
            ])
        source_table = Table(source_data, colWidths=[5 * cm, 5 * cm, 5 * cm])
        source_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e2ec")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(source_table)

        elements.append(Paragraph("四、最近告警记录", h1_style))
        alerts = await db.alerts.find(
            {"monitor_id": monitor_id},
            sort=[("created_at", -1)],
            limit=10,
        ).to_list(length=10)

        if alerts:
            alert_data = [["告警类型", "消息", "创建时间"]]
            for alert in alerts:
                alert_data.append([
                    alert.get("alert_type", ""),
                    alert.get("message", "")[:50],
                    alert.get("created_at", "").strftime("%m-%d %H:%M"),
                ])
            alert_table = Table(alert_data, colWidths=[3 * cm, 8 * cm, 4 * cm])
            alert_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e94560")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e2ec")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(alert_table)
        else:
            elements.append(Paragraph("暂无告警记录", normal_style))

        elements.append(Paragraph("五、最近采集数据样本", h1_style))
        recent_data = await db.collected_data.find(
            {"monitor_id": monitor_id},
            sort=[("collected_at", -1)],
            limit=5,
        ).to_list(length=5)

        for idx, d in enumerate(recent_data, 1):
            sentiment_color = "#2ecc71" if d["sentiment_label"] == "positive" else (
                "#e74c3c" if d["sentiment_label"] == "negative" else "#f39c12"
            )
            elements.append(Paragraph(f"样本 {idx}", h2_style))
            elements.append(Paragraph(
                f"<b>标题：</b>{d.get('title', '')}<br/>"
                f"<b>来源：</b>{d.get('source_type', '')} | "
                f"<b>作者：</b>{d.get('author', '')} | "
                f"<b>情感：</b><font color='{sentiment_color}'>{d['sentiment_label']} ({d['sentiment_score']:.2f})</font><br/>"
                f"<b>内容：</b>{d.get('content', '')[:150]}...",
                normal_style,
            ))
            elements.append(Spacer(1, 0.3 * cm))

        elements.append(HRFlowable(
            width="100%", thickness=1, color=colors.HexColor("#d9e2ec"),
            spaceBefore=1 * cm, spaceAfter=0.5 * cm,
        ))
        elements.append(Paragraph(
            "<i>本报告由舆情监控系统自动生成，数据仅供参考。</i>",
            ParagraphStyle(
                "Footer",
                parent=styles["Italic"],
                fontName=font_name,
                fontSize=8,
                alignment=1,
                textColor=colors.grey,
            ),
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
