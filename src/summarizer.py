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
        from datetime import datetime
        today_str = datetime.now().strftime("%Y. %m. %d (%a)")
        
        # Base Style
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f6f8; }}
                .container {{ max-width: 700px; margin: 0 auto; background: #ffffff; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                .header {{ background: linear-gradient(135deg, #1a2980 0%, #26d0ce 100%); padding: 40px 30px; text-align: center; color: white; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }}
                .header p {{ margin: 10px 0 0; opacity: 0.9; font-size: 15px; }}
                .date-badge {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 13px; margin-bottom: 15px; }}
                .content {{ padding: 30px; }}
                .section-title {{ display: flex; align-items: center; margin: 40px 0 20px; font-size: 20px; font-weight: 700; color: #1a202c; border-bottom: 2px solid #1a202c; padding-bottom: 10px; }}
                .section-title span {{ margin-right: 8px; }}
                
                .topic-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); transition: transform 0.2s; }}
                .topic-header {{ margin-bottom: 20px; border-bottom: 1px dashed #cbd5e0; padding-bottom: 15px; }}
                .topic-tag {{ display: inline-block; background: #ebf8ff; color: #2b6cb0; font-size: 12px; font-weight: bold; padding: 4px 8px; border-radius: 4px; margin-bottom: 8px; }}
                .topic-title {{ font-size: 22px; color: #2d3748; margin: 0 0 10px 0; font-weight: 700; line-height: 1.3; }}
                .topic-reason {{ font-size: 15px; color: #4a5568; background-color: #f7fafc; padding: 12px; border-radius: 8px; border-left: 4px solid #4299e1; }}
                
                .article-item {{ margin-top: 20px; padding-left: 15px; position: relative; }}
                .article-title {{ font-size: 17px; font-weight: 600; color: #2d3748; display: block; margin-bottom: 6px; text-decoration: none; }}
                .article-meta {{ font-size: 12px; color: #718096; margin-bottom: 8px; }}
                .article-summary {{ font-size: 14px; color: #4a5568; margin-bottom: 10px; line-height: 1.5; }}
                
                .key-points {{ background-color: #f0fff4; border-radius: 8px; padding: 15px; margin-top: 10px; }}
                .key-points h4 {{ margin: 0 0 8px 0; font-size: 13px; color: #276749; text-transform: uppercase; letter-spacing: 0.5px; }}
                .key-points ul {{ margin: 0; padding-left: 20px; }}
                .key-points li {{ font-size: 14px; color: #2f855a; margin-bottom: 4px; }}
                
                .category-header {{ background-color: #edf2f7; padding: 8px 15px; border-radius: 6px; font-weight: bold; color: #2d3748; font-size: 16px; margin-top: 30px; margin-bottom: 15px; }}
                .category-article {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee; }}
                .category-article:last-child {{ border-bottom: none; }}
                .category-article-title {{ font-size: 15px; font-weight: 600; color: #2d3748; text-decoration: none; display: block; margin-bottom: 4px; }}
                .category-article-meta {{ font-size: 12px; color: #a0aec0; margin-bottom: 4px; }}
                .category-article-summary {{ font-size: 13px; color: #718096; line-height: 1.4; }}
                
                .footer {{ background: #2d3748; color: #a0aec0; text-align: center; padding: 30px; font-size: 13px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="date-badge">{today_str}</div>
                    <h1>NewsAgent Daily Brief</h1>
                    <p>오늘의 AI 트렌드를 가장 빠르게 전달해 드립니다.</p>
                </div>
                
                <div class="content">
                    <div class="section-title">
                        <span>🔥</span> Today's Top 5 Topics
                    </div>
        """
        
        used_indices = set()
        
        # Top Topics Section
        for idx, topic in enumerate(topics):
            html += f"""
            <div class="topic-card">
                <div class="topic-header">
                    <span class="topic-tag">TOPIC {idx+1:02d}</span>
                    <h3 class="topic-title">{topic.get('topic_title')}</h3>
                    <div class="topic-reason">
                        {topic.get('topic_reason')}
                    </div>
                </div>
            """
            
            for news_idx in topic.get('related_news_indices', []):
                if 0 <= news_idx < len(all_news):
                    news = all_news[news_idx]
                    used_indices.add(news_idx)
                    
                    # Analysis (Bullet points)
                    analysis_html = ""
                    if 'analysis' in news and isinstance(news['analysis'], list):
                        analysis_html = '<div class="key-points"><h4>Key Insights</h4><ul>' + \
                                      "".join([f"<li>{point}</li>" for point in news['analysis']]) + \
                                      '</ul></div>'
                    elif 'analysis' in news:
                         analysis_html = f'<div class="key-points"><h4>Key Insights</h4><p>{news["analysis"]}</p></div>'

                    html += f"""
                    <div class="article-item">
                        <a href="{news['link']}" class="article-title" target="_blank">{news.get('title_korean', news['title'])}</a>
                        <div class="article-meta">{news.get('source', 'Source')} | {news.get('published_at', '')[:10]}</div>
                        <div class="article-summary">{news.get('one_line_summary', '')}</div>
                        {analysis_html}
                    </div>
                    """
            html += "</div>"

        # Category Section (Remaining News)
        html += """
            <div class="section-title">
                <span>📂</span> More News by Category
            </div>
        """
        
        # Group remaining news by category
        news_by_category = {}
        for idx, news in enumerate(all_news):
            if idx not in used_indices:
                cat = news.get('category', 'Others')
                if cat not in news_by_category:
                    news_by_category[cat] = []
                news_by_category[cat].append(news)
        
        for category, news_list in news_by_category.items():
            if not news_list: continue
            
            html += f'<div class="category-header">{category}</div>'
            
            for news in news_list:
                html += f"""
                <div class="category-article">
                    <a href="{news['link']}" class="category-article-title" target="_blank">{news.get('title_korean', news['title'])}</a>
                    <div class="category-article-meta">{news.get('source', '')}</div>
                    <div class="category-article-summary">{news.get('one_line_summary', '')}</div>
                </div>
                """

        # Footer
        html += """
                </div>
                <div class="footer">
                    Generated by <strong>NewsAgent</strong> with Gemini 2.5 Flash<br>
                    &copy; 2025 NewsAgent
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
