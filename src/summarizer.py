import json
import time
import google.generativeai as genai
from typing import List, Dict, Any
from config import settings

class NewsAnalyst:
    """
    뉴스를 5개씩 묶어서 상세 요약 및 분석을 수행하는 역할
    """
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            # GitHub Actions 등에서는 환경변수로 바로 들어올 수 있음
            pass 
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

    def analyze_batch(self, news_batch: List[Dict]) -> List[Dict]:
        """
        뉴스 배치(약 5개)를 받아 각각에 대한 상세 분석 결과를 반환
        """
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
            
            # JSON 파싱
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            analyzed_list = json.loads(text.strip())
            
            # 결과 보정 (원본 링크가 누락될 수 있으므로 다시 매핑)
            final_results = []
            for item in analyzed_list:
                idx = item.get('index')
                if idx is not None and 0 <= idx < len(news_batch):
                    # 원본 정보와 결합
                    combined = news_batch[idx].copy()
                    combined.update(item) # 요약 정보 덮어쓰기
                    final_results.append(combined)
            
            return final_results

        except Exception as e:
            print(f"Error in analyzing batch: {e}")
            # 에러 시 원본이라도 반환 (요약 없이)
            return news_batch

    def analyze_all(self, all_news: List[Dict], batch_size=5) -> List[Dict]:
        """
        전체 뉴스를 배치 단위로 나누어 처리
        """
        print(f"Analyzing {len(all_news)} news items in batches of {batch_size}...")
        results = []
        
        for i in range(0, len(all_news), batch_size):
            batch = all_news[i:i+batch_size]
            print(f"  - Processing batch {i//batch_size + 1} ({len(batch)} items)...")
            
            analyzed_batch = self.analyze_batch(batch)
            results.extend(analyzed_batch)
            
            # Rate Limit 방지를 위한 짧은 대기 (Gemini 무료 티어 고려)
            time.sleep(2)
            
        return results


class NewsCurator:
    """
    (Placeholder) 나중에 구현 예정
    """
    def select_top_topics(self, analyzed_news: List[Dict]) -> List[Dict]:
        pass

class ReportBuilder:
    """
    (Placeholder) 나중에 구현 예정
    """
    pass
