import os
from datetime import datetime
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from src.utils.font_manager import ensure_korean_font

class PDFBuilder:
    def __init__(self):
        self.font_path = ensure_korean_font()
        if self.font_path:
            pdfmetrics.registerFont(TTFont('NanumGothic', self.font_path))
            self.font_name = 'NanumGothic'
        else:
            self.font_name = 'Helvetica' # Fallback (한글 깨짐)

        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='TitleKorean',
            fontName=self.font_name,
            fontSize=24,
            leading=30,
            alignment=1, # Center
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='Heading1Korean',
            fontName=self.font_name,
            fontSize=18,
            leading=22,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#1a2980')
        ))
        self.styles.add(ParagraphStyle(
            name='Heading2Korean',
            fontName=self.font_name,
            fontSize=14,
            leading=18,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#2c3e50')
        ))
        self.styles.add(ParagraphStyle(
            name='BodyKorean',
            fontName=self.font_name,
            fontSize=10,
            leading=16,
            spaceAfter=8
        ))
        self.styles.add(ParagraphStyle(
            name='SmallKorean',
            fontName=self.font_name,
            fontSize=8,
            leading=12,
            textColor=colors.gray
        ))

    def build_pdf(self, topics: List[Dict], all_news: List[Dict], output_filename="report.pdf"):
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=A4,
            rightMargin=50, leftMargin=50,
            topMargin=50, bottomMargin=50
        )
        
        story = []
        today_str = datetime.now().strftime("%Y. %m. %d (%A)")

        # 1. Cover Page
        story.append(Spacer(1, 100))
        story.append(Paragraph("NewsAgent Daily Brief", self.styles['TitleKorean']))
        story.append(Paragraph(f"{today_str}", self.styles['Heading1Korean']))
        story.append(Spacer(1, 50))
        story.append(Paragraph("오늘의 AI 트렌드 종합 리포트", self.styles['BodyKorean']))
        story.append(PageBreak())

        # 2. Top 5 Topics Section
        story.append(Paragraph("🔥 Today's Top 5 Topics", self.styles['Heading1Korean']))
        
        used_indices = set()
        
        for idx, topic in enumerate(topics):
            # Topic Title
            story.append(Paragraph(f"{idx+1}. {topic.get('topic_title')}", self.styles['Heading2Korean']))
            
            # Reason Box (Simple Background simulation using Table)
            reason_text = Paragraph(f"💡 {topic.get('topic_reason')}", self.styles['BodyKorean'])
            data = [[reason_text]]
            t = Table(data, colWidths=[450])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f7fafc')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e0')),
                ('PADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))

            # Related Articles
            for news_idx in topic.get('related_news_indices', []):
                if 0 <= news_idx < len(all_news):
                    news = all_news[news_idx]
                    used_indices.add(news_idx)
                    
                    title = news.get('title_korean', news['title'])
                    summary = news.get('one_line_summary', '')
                    source = news.get('source', '')
                    link = news.get('link', '')

                    # Article Block
                    story.append(Paragraph(f"• {title}", self.styles['BodyKorean']))
                    story.append(Paragraph(f"   {summary}", self.styles['SmallKorean']))
                    story.append(Paragraph(f"   <a href='{link}' color='blue'>{source} (Link)</a>", self.styles['SmallKorean']))
                    story.append(Spacer(1, 5))
            
            story.append(Spacer(1, 15))

        story.append(PageBreak())

        # 3. Full Category News Section
        story.append(Paragraph("📂 More News by Category", self.styles['Heading1Korean']))

        # Group remaining news
        news_by_category = {}
        for idx, news in enumerate(all_news):
            if idx not in used_indices:
                cat = news.get('category', 'Others')
                if cat not in news_by_category:
                    news_by_category[cat] = []
                news_by_category[cat].append(news)

        for category, news_list in news_by_category.items():
            if not news_list: continue
            
            story.append(Paragraph(f"📌 {category}", self.styles['Heading2Korean']))
            
            for news in news_list:
                title = news.get('title_korean', news['title'])
                summary = news.get('one_line_summary', '')
                source = news.get('source', '')
                link = news.get('link', '')
                
                # Simple List Item
                story.append(Paragraph(f"<b>{title}</b> | <font color='gray'>{source}</font>", self.styles['BodyKorean']))
                story.append(Paragraph(f"{summary}", self.styles['SmallKorean']))
                story.append(Paragraph(f"<a href='{link}' color='blue'>Read More</a>", self.styles['SmallKorean']))
                story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 10))

        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generated by NewsAgent", self.styles['SmallKorean']))

        # Build PDF
        doc.build(story)
        print(f"PDF Generated: {output_filename}")
        return output_filename

