import json
import time
from typing import List, Dict, Any
import google.generativeai as genai
from config import settings

class NewsAnalyst:
    """
    뉴스를 5개씩 묶어서 상세 요약 및 분석을 수행하는 역할
    """
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

    def analyze_batch(self, news_batch: List[Dict]) -> List[Dict]:
        if not news_batch:
            return []

        # 프롬프트 구성
        news_text = ""
        for idx, news in enumerate(news_batch):
            news_text += f"""
            [News {idx}]
            Title: {news['title']}
            Source: {news.get('source', 'Unknown')}
            Link: {news['link']}
            Original Summary: {news.get('summary', '')}
            --------------------------------
            """

        prompt = f"""
        You are an expert AI Tech Analyst.
        Below are {len(news_batch)} AI-related news articles.
        
        For EACH article, please provide a structured summary.
        
        Your output must be a valid JSON list of objects.
        Format:
        [
            {{
                "index": 0,
                "title_korean": "Translate title to Korean",
                "one_line_summary": "One sentence summary in Korean (Easy to understand)",
                "analysis": "3 bullet points explaining the key details and why it matters (in Korean)",
                "original_link": "Use the Link provided in input"
            }},
            ...
        ]

        Input News:
        {news_text}
        """

        try:
            response = self.model.generate_content(prompt)
            
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            analyzed_list = json.loads(text.strip())
            
            final_results = []
            for item in analyzed_list:
                idx = item.get('index')
                if idx is not None and 0 <= idx < len(news_batch):
                    combined = news_batch[idx].copy()
                    combined.update(item)
                    final_results.append(combined)
            
            return final_results

        except Exception as e:
            print(f"Error in analyzing batch: {e}")
            return news_batch

    def analyze_all(self, all_news: List[Dict], batch_size=5) -> List[Dict]:
        print(f"Analyzing {len(all_news)} news items in batches of {batch_size}...")
        results = []
        
        for i in range(0, len(all_news), batch_size):
            batch = all_news[i:i+batch_size]
            # print(f"  - Processing batch {i//batch_size + 1} ({len(batch)} items)...")
            analyzed_batch = self.analyze_batch(batch)
            results.extend(analyzed_batch)
            time.sleep(1) # Rate limit 고려
            
        return results


class NewsCurator:
    """
    분석된 뉴스 전체를 보고 Top N 토픽을 선정하는 역할
    """
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

    def select_top_topics(self, analyzed_news: List[Dict]) -> List[Dict]:
        """
        분석된 뉴스 리스트를 받아 Top 5 토픽 선정
        """
        if not analyzed_news:
            return []
            
        # 입력 데이터 최소화 (토큰 절약)
        input_text = ""
        for idx, news in enumerate(analyzed_news):
            title = news.get('title_korean', news['title'])
            summary = news.get('one_line_summary', '')
            input_text += f"[{idx}] {title} : {summary}\n"

        prompt = f"""
        You are the Chief Editor of an AI News Letter.
        Below is a list of today's AI news (analyzed summaries).
        
        Your task is to select the **Top 5 Most Important Topics** that represent today's AI trends.
        Group related news articles under each topic.
        
        Output must be a valid JSON list.
        Format:
        [
            {{
                "topic_title": "Eye-catching Headline in Korean",
                "topic_reason": "Why this is important (in Korean)",
                "related_news_indices": [index1, index2, ...]
            }},
            ...
        ]
        
        News List:
        {input_text}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            topics = json.loads(text.strip())
            return topics
            
        except Exception as e:
            print(f"Error in curator: {e}")
            return []


class ReportBuilder:
    """
    최종 HTML 이메일 본문을 생성하는 역할
    """
    def build_html(self, topics: List[Dict], all_news: List[Dict]) -> str:
        html = """
        <html>
        <head>
            <style>
                body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }
                .header { text-align: center; margin-bottom: 40px; background-color: #f8f9fa; padding: 20px; border-radius: 8px; }
                .topic-card { background: #fff; border: 1px solid #e1e4e8; border-radius: 8px; padding: 20px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
                .topic-title { font-size: 1.4em; color: #0366d6; margin-top: 0; font-weight: bold; }
                .topic-reason { color: #586069; font-style: italic; margin-bottom: 15px; }
                .news-item { margin-bottom: 15px; padding-left: 15px; border-left: 3px solid #0366d6; }
                .news-title { font-weight: bold; font-size: 1.1em; display: block; margin-bottom: 5px; }
                .news-summary { color: #444; font-size: 0.95em; margin-bottom: 5px; }
                .news-analysis { font-size: 0.9em; color: #666; background: #f1f8ff; padding: 10px; border-radius: 4px; }
                .news-link { font-size: 0.85em; color: #0366d6; text-decoration: none; }
                .footer { margin-top: 50px; text-align: center; font-size: 0.8em; color: #888; border-top: 1px solid #eee; padding-top: 20px; }
                .full-list-section { margin-top: 50px; }
                .full-list-item { margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📰 오늘의 AI 트렌드 리포트</h1>
                <p>NewsAgent가 엄선한 최신 AI 뉴스 브리핑입니다.</p>
            </div>
            
            <h2>🔥 Top 5 Hot Topics</h2>
        """
        
        used_indices = set()
        
        # Top Topics Section
        for topic in topics:
            html += f"""
            <div class="topic-card">
                <div class="topic-title">{topic.get('topic_title')}</div>
                <div class="topic-reason">💡 {topic.get('topic_reason')}</div>
            """
            
            for idx in topic.get('related_news_indices', []):
                if 0 <= idx < len(all_news):
                    news = all_news[idx]
                    used_indices.add(idx)
                    
                    # Bullet points (analysis) 처리
                    analysis_html = ""
                    if 'analysis' in news and isinstance(news['analysis'], list):
                        analysis_html = "<ul>" + "".join([f"<li>{point}</li>" for point in news['analysis']]) + "</ul>"
                    elif 'analysis' in news:
                        analysis_html = f"<p>{news['analysis']}</p>"
                        
                    html += f"""
                    <div class="news-item">
                        <span class="news-title">{news.get('title_korean', news['title'])}</span>
                        <div class="news-summary">{news.get('one_line_summary', '')}</div>
                        <div class="news-analysis">{analysis_html}</div>
                        <a href="{news['link']}" class="news-link" target="_blank">원문 보기 ({news.get('source', 'Source')}) →</a>
                    </div>
                    """
            html += "</div>"
            
        # Full List Section (나머지 뉴스)
        html += """
            <div class="full-list-section">
                <h2>📋 전체 뉴스 리스트 (Other News)</h2>
        """
        
        for idx, news in enumerate(all_news):
            if idx not in used_indices:
                html += f"""
                <div class="full-list-item">
                    <strong>{news.get('title_korean', news['title'])}</strong> 
                    <span style="color: #888; font-size: 0.9em;">- {news.get('source', '')}</span><br>
                    <span style="font-size: 0.9em;">{news.get('one_line_summary', '')}</span><br>
                    <a href="{news['link']}" style="font-size: 0.85em; color: #0366d6;">Link</a>
                </div>
                """
                
        html += """
            </div>
            <div class="footer">
                Generated by NewsAgent with Gemini 2.5 Flash<br>
                &copy; 2025 NewsAgent
            </div>
        </body>
        </html>
        """
        
        return html
