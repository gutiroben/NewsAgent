import json
import time
from typing import List, Dict, Any
import google.generativeai as genai
from config import settings

class NewsAnalyst:
    """
    뉴스를 3개씩 묶어서 심층 분석(Deep Dive)을 수행하는 역할
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
            Original Summary: {news.get('summary', '')}
            --------------------------------
            """

        prompt = f"""
        You are an expert AI Tech Analyst.
        Below are {len(news_batch)} AI-related news articles.
        
        For EACH article, provide a "Deep Dive" analysis report.
        
        Output must be a valid JSON list.
        Format:
        [
            {{
                "index": 0,
                "title_korean": "Translate title to Korean (Natural & Professional)",
                "core_summary": "2-3 sentences summarizing the main point (Korean). Explain WHY this is important.",
                "detailed_explanation": "Detailed explanation with numbered points (①, ②, ③...). Use subheadings if needed. This part should be comprehensive enough for the reader to understand the whole context without reading the original article. (Korean)"
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

    def analyze_all(self, all_news: List[Dict], batch_size=3) -> List[Dict]:
        print(f"Analyzing {len(all_news)} news items in batches of {batch_size}...")
        results = []
        
        for i in range(0, len(all_news), batch_size):
            batch = all_news[i:i+batch_size]
            analyzed_batch = self.analyze_batch(batch)
            results.extend(analyzed_batch)
            time.sleep(1) # Rate limit 고려
            
        return results

