import json
from typing import List, Dict
import google.generativeai as genai
from config import settings

class NewsCurator:
    """
    분석된 뉴스 전체를 보고 Top N 기사를 선정하는 역할
    """
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

    def select_top_articles(self, analyzed_news: List[Dict]) -> List[Dict]:
        """
        분석된 뉴스 리스트를 받아 Top 5 기사 선정
        """
        if not analyzed_news:
            return []
            
        # 입력 데이터 최소화 (Index, Title, Core Summary만 사용)
        input_text = ""
        for idx, news in enumerate(analyzed_news):
            title = news.get('title_korean', news['title'])
            summary = news.get('core_summary', '') # 핵심 요약만 사용
            input_text += f"[{idx}] {title} : {summary}\n"

        prompt = f"""
        You are the Chief Editor of an AI News Letter.
        Below is a list of today's AI news headlines and summaries.
        
        Your task is to select the **Top 5 Most Important Articles** that represent today's key AI trends.
        Do NOT group them. Just select the 5 specific articles.
        
        Output must be a valid JSON list.
        Format:
        [
            {{
                "article_index": 0,  // Integer
                "selection_reason": "Why this article is selected (in Korean)"
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
                
            selected_list = json.loads(text.strip())
            
            # 결과 매핑: 선정된 기사 정보를 찾아서 리스트로 반환
            final_top5 = []
            for item in selected_list:
                idx = item.get('article_index')
                if idx is not None and 0 <= idx < len(analyzed_news):
                    article = analyzed_news[idx].copy()
                    article['selection_reason'] = item.get('selection_reason')
                    final_top5.append(article)
                    
            return final_top5
            
        except Exception as e:
            print(f"Error in curator: {e}")
            return []

