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
            # 다양한 관점의 분석을 위해 temperature=0.4 설정
            generation_config = {"temperature": 0.4}
            response = self.model.generate_content(prompt, generation_config=generation_config)
            
            text = response.text
            # 마크다운 코드 블록 제거 (더 견고하게)
            clean_text = text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:]
            
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            
            clean_text = clean_text.strip()
            
            try:
                analyzed_list = json.loads(clean_text)
            except json.JSONDecodeError as je:
                print(f"JSON Parsing Error in Analyst: {je}")
                print(f"Raw Text from Gemini:\n{text}") # 디버깅용 원본 출력
                return news_batch # 파싱 실패 시 원본 반환

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

