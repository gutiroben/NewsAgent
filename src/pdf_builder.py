import os
import re
from datetime import datetime
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, ListFlowable, ListItem
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from src.utils.font_manager import ensure_korean_font

# 목차(TOC) 생성을 위한 커스텀 DocTemplate (필요시 확장 가능하지만 SimpleDocTemplate으로 시도)
# ReportLab TOC는 MultiBuild가 필요함.

class PDFBuilder:
    def __init__(self):
        self.font_path = ensure_korean_font()
        if self.font_path:
            pdfmetrics.registerFont(TTFont('NanumGothic', self.font_path))
            self.font_name = 'NanumGothic'
        else:
            self.font_name = 'Helvetica'

        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='TitleKorean', fontName=self.font_name, fontSize=26, leading=32, alignment=1, spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='SubtitleKorean', fontName=self.font_name, fontSize=12, leading=16, alignment=1, textColor=colors.gray
        ))
        self.styles.add(ParagraphStyle(
            name='Heading1Korean', fontName=self.font_name, fontSize=18, leading=24, spaceBefore=20, spaceAfter=10, textColor=colors.HexColor('#1a2980')
        ))
        self.styles.add(ParagraphStyle(
            name='Heading2Korean', fontName=self.font_name, fontSize=14, leading=18, spaceBefore=15, spaceAfter=8, textColor=colors.HexColor('#2d3748')
        ))
        self.styles.add(ParagraphStyle(
            name='ArticleTitle', fontName=self.font_name, fontSize=16, leading=20, spaceBefore=15, spaceAfter=8, textColor=colors.HexColor('#2d3748')
        ))
        self.styles.add(ParagraphStyle(
            name='MetaInfo', fontName=self.font_name, fontSize=9, leading=12, textColor=colors.gray, spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='CoreSummary', fontName=self.font_name, fontSize=11, leading=16, backColor=colors.HexColor('#f7fafc'), borderPadding=10, spaceAfter=15
        ))
        # 기존 BodyText가 있으면 업데이트, 없으면 추가
        if 'BodyText' in self.styles:
            self.styles['BodyText'].fontName = self.font_name
            self.styles['BodyText'].fontSize = 10
            self.styles['BodyText'].leading = 16
            self.styles['BodyText'].spaceAfter = 10
        else:
            self.styles.add(ParagraphStyle(
                name='BodyText', fontName=self.font_name, fontSize=10, leading=16, spaceAfter=10
            ))
            
        self.styles.add(ParagraphStyle(
            name='TOCEntry', fontName=self.font_name, fontSize=11, leading=14, spaceAfter=5
        ))

    def build_pdf(self, top5_articles: List[Dict], all_news: List[Dict], output_filename="report.pdf"):
        doc = MyDocTemplate(output_filename, pagesize=A4)
        story = []
        today_str = datetime.now().strftime("%Y. %m. %d (%A)")

        # 1. Cover Page
        story.append(Spacer(1, 100))
        story.append(Paragraph("NewsAgent Daily Brief", self.styles['TitleKorean']))
        story.append(Paragraph(f"{today_str}", self.styles['TitleKorean']))
        story.append(Spacer(1, 30))
        story.append(Paragraph("Deep Dive into AI Trends", self.styles['SubtitleKorean']))
        story.append(PageBreak())

        # 2. Manual Table of Contents (with Links)
        story.append(Paragraph("Table of Contents", self.styles['Heading1Korean']))
        story.append(Spacer(1, 20))

        # Top 5 Links
        story.append(Paragraph("🔥 Top 5 Insights", self.styles['Heading2Korean']))
        for idx, article in enumerate(top5_articles):
            title = article.get('title_korean', article['title'])
            # Link to Anchor 'TOP5_{idx}'
            link_text = f"<a href='#TOP5_{idx}' color='black'>{idx+1}. {title}</a>"
            story.append(Paragraph(link_text, self.styles['TOCEntry']))
        
        story.append(Spacer(1, 10))
        
        # Category Links
        story.append(Paragraph("📂 News by Category", self.styles['Heading2Korean']))
        
        # Organize data for TOC
        processed_indices = set()
        for article in top5_articles:
             if 'link' in article: processed_indices.add(article['link'])

        news_by_category = {}
        for news in all_news:
            if news.get('link') in processed_indices: continue
            cat = news.get('category', 'Others')
            if cat not in news_by_category: news_by_category[cat] = []
            news_by_category[cat].append(news)

        # Create TOC for Categories
        cat_idx = 0
        for category, news_list in news_by_category.items():
            if not news_list: continue
            
            # Category Title
            clean_cat = category.replace('&', '&amp;')
            story.append(Paragraph(f"📌 {clean_cat}", self.styles['Heading2Korean']))
            
            # Article Titles in TOC
            for art_idx, news in enumerate(news_list):
                title = news.get('title_korean', news['title'])
                # Link to Anchor 'CAT_{cat_idx}_ART_{art_idx}'
                # 제목이 길면 자르기
                if len(title) > 60: title = title[:60] + "..."
                clean_title = title.replace('&', '&amp;')
                
                link_text = f"<a href='#CAT_{cat_idx}_ART_{art_idx}' color='black'>• {clean_title}</a>"
                story.append(Paragraph(link_text, self.styles['TOCEntry']))
                
            story.append(Spacer(1, 10))
            cat_idx += 1

        story.append(PageBreak())

        # 3. Top 5 Deep Dive Body
        story.append(Paragraph("🔥 Top 5 Insights", self.styles['Heading1Korean']))
        
        for idx, article in enumerate(top5_articles):
            # Set Anchor 'TOP5_{idx}'
            anchor_tag = f'<a name="TOP5_{idx}"/>'
            self._add_article_to_story(story, article, rank=idx+1, anchor=anchor_tag)
            
            if (idx + 1) % 2 == 0:
                story.append(PageBreak())
            else:
                story.append(Spacer(1, 30))

        story.append(PageBreak())

        # 4. Full News by Category Body
        story.append(Paragraph("📂 Full News by Category", self.styles['Heading1Korean']))
        
        cat_idx = 0
        for category, news_list in news_by_category.items():
            if not news_list: continue
            
            clean_cat = category.replace('&', '&amp;')
            story.append(Paragraph(f"📌 {clean_cat}", self.styles['Heading1Korean']))
            
            for art_idx, news in enumerate(news_list):
                # Set Anchor 'CAT_{cat_idx}_ART_{art_idx}'
                anchor_tag = f'<a name="CAT_{cat_idx}_ART_{art_idx}"/>'
                self._add_article_to_story(story, news, is_simple=False, anchor=anchor_tag)
                story.append(Spacer(1, 20))
            
            story.append(PageBreak())
            cat_idx += 1

        # Build
        doc.build(story)
        print(f"PDF Generated: {output_filename}")
        return output_filename

    def _clean_markdown(self, text):
        """Markdown 문법을 ReportLab이 이해할 수 있는 HTML 태그로 변환"""
        if not text: return ""
        
        # 1. Bold: **text** -> <b>text</b>
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # 2. List: * item or - item -> • item (줄바꿈은 나중에 처리)
        # 문장 시작 부분의 * 나 - 를 Bullet으로 변경
        text = re.sub(r'^\s*[\*\-]\s+', '• ', text, flags=re.MULTILINE)
        
        # 3. Headers: ### Title -> <b>Title</b>
        text = re.sub(r'###\s*(.*)', r'<b>\1</b>', text)
        
        return text

    def _add_article_to_story(self, story, article, rank=None, is_simple=False, anchor=""):
        title = article.get('title_korean', article['title'])
        summary = article.get('core_summary', '')
        detail = article.get('detailed_explanation', '')
        source = article.get('source', '')
        link = article.get('link', '')
        
        if rank:
            header = f"{anchor}{rank}. {title}"
        else:
            header = f"{anchor}{title}"
            
        story.append(Paragraph(header, self.styles['ArticleTitle']))
        story.append(Paragraph(f"{source} | <a href='{link}' color='blue'>Original Link</a>", self.styles['MetaInfo']))
        
        if summary:
            # Summary도 Markdown 처리
            clean_summary = self._clean_markdown(summary)
            story.append(Paragraph(f"<b>[핵심 요지]</b><br/>{clean_summary}", self.styles['CoreSummary']))

        if detail:
            # Markdown Cleaning
            clean_detail = self._clean_markdown(detail)
            formatted_detail = clean_detail.replace('\n', '<br/>')
            story.append(Paragraph(formatted_detail, self.styles['BodyText']))


# TOC 지원을 위한 커스텀 템플릿
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame

class MyDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        "Registers TOC entries."
        if flowable.__class__.__name__ == 'Paragraph':
            text = flowable.getPlainText()
            style = flowable.style.name
            if style == 'Heading1Korean':
                self.notify('TOCEntry', (0, text, self.page))
            elif style == 'ArticleTitle':
                # 제목이 너무 길면 자르기
                if len(text) > 50: text = text[:50] + "..."
                self.notify('TOCEntry', (1, text, self.page))

