import os
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

        # 2. Table of Contents (TOC)
        story.append(Paragraph("Table of Contents", self.styles['Heading1Korean']))
        toc = TableOfContents()
        toc.levelStyles = [self.styles['TOCEntry']]
        story.append(toc)
        story.append(PageBreak())

        # 3. Top 5 Deep Dive
        story.append(Paragraph("🔥 Top 5 Insights", self.styles['Heading1Korean']))
        
        # 중복 방지용 Set
        processed_indices = set()

        for idx, article in enumerate(top5_articles):
            self._add_article_to_story(story, article, rank=idx+1)
            # 원본 인덱스 추적 (나중에 중복 출력 방지)
            # article['index']가 있으면 좋지만, 없으면 내용 매칭 등 필요. 
            # 여기서는 Top5는 무조건 제외 리스트에 추가
            if 'link' in article:
                processed_indices.add(article['link'])
            
            # 2개마다 페이지 넘김 (가독성)
            if (idx + 1) % 2 == 0:
                story.append(PageBreak())
            else:
                story.append(Spacer(1, 30))

        story.append(PageBreak())

        # 4. Full News by Category
        story.append(Paragraph("📂 Full News by Category", self.styles['Heading1Korean']))
        
        # Grouping
        news_by_category = {}
        for news in all_news:
            if news.get('link') in processed_indices:
                continue
            cat = news.get('category', 'Others')
            if cat not in news_by_category:
                news_by_category[cat] = []
            news_by_category[cat].append(news)

        for category, news_list in news_by_category.items():
            if not news_list: continue
            
            story.append(Paragraph(f"📌 {category}", self.styles['Heading1Korean']))
            
            for news in news_list:
                self._add_article_to_story(story, news, is_simple=False) # 모두 상세 버전으로 출력
                story.append(Spacer(1, 20))
            
            story.append(PageBreak())

        # PDF 생성 (MultiBuild for TOC)
        doc.multiBuild(story)
        print(f"PDF Generated: {output_filename}")
        return output_filename

    def _add_article_to_story(self, story, article, rank=None, is_simple=False):
        title = article.get('title_korean', article['title'])
        summary = article.get('core_summary', '')
        detail = article.get('detailed_explanation', '')
        source = article.get('source', '')
        link = article.get('link', '')
        
        # Anchor for TOC (나중에 구현 가능, 현재는 제목 스타일만 적용)
        # TOC 자동 생성을 위해 Paragraph에 태그 추가 필요
        
        if rank:
            header = f"{rank}. {title}"
        else:
            header = title
            
        # 제목 (TOC에 자동 등록되려면 텍스트만 쓰는 게 아니라 flowable 조작이 필요하지만
        # ReportLab의 Paragraph를 쓰면 afterFlowable 등을 써야함.
        # 여기서는 간단히 텍스트만 추가하고 TOC는 multiBuild가 알아서 h1, h2 스타일을 잡도록 설정해야 함.
        # 하지만 MyDocTemplate에서 afterFlowable을 오버라이드해야 함.
        # 일단은 복잡한 TOC 링크 대신 심플하게 갑니다.)
        
        story.append(Paragraph(header, self.styles['ArticleTitle']))
        story.append(Paragraph(f"{source} | <a href='{link}' color='blue'>Original Link</a>", self.styles['MetaInfo']))
        
        # 핵심 요약 박스
        if summary:
            story.append(Paragraph(f"<b>[핵심 요지]</b><br/>{summary}", self.styles['CoreSummary']))

        # 상세 설명 (Markdown 줄바꿈 처리)
        if detail:
            # detail 텍스트 내의 줄바꿈을 <br/>로 변환
            formatted_detail = detail.replace('\n', '<br/>')
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

