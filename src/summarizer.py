import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Any

# 환경 변수 로드
load_dotenv()

class NewsCurator:
    """
    전체 뉴스 목록에서 핵심 토픽을 선정하고 그룹핑하는 역할
    """
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in .env file")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def select_top_topics(self, news_list: List[Dict]) -> List[Dict]:
        """
        뉴스 리스트를 받아 Top N개의 토픽을 선정하여 반환
        Return 구조 예시:
        [
            {
                "topic": "OpenAI GPT-5 출시 루머",
                "reason": "AI 업계에 가장 큰 파급력을 가짐",
                "related_news_indices": [0, 4, 12]  # 입력 리스트의 인덱스
            },
            ...
        ]
        """
        if not news_list:
            return []
            
        # 1. 프롬프트 구성
        news_text = ""
        for idx, news in enumerate(news_list):
            news_text += f"[{idx}] {news['title']} (Source: {news['source']})\n"
            
        prompt = f"""
        You are an expert AI Tech Analyst.
        Below is a list of AI-related news articles collected today.
        
        Your task is to:
        1. Identify the top 3-5 most important topics/themes from this list.
        2. Group related news articles under each topic.
        3. Ignore irrelevant or minor news.
        
        Output must be a valid JSON list of objects.
        JSON Format:
        [
            {{
                "topic": "Brief Topic Title",
                "reason": "One sentence explaining why this is important",
                "related_news_indices": [index1, index2, ...]
            }}
        ]
        
        News List:
        {news_text}
        """
        
        try:
            # 2. API 호출
            response = self.model.generate_content(prompt)
            
            # 3. 결과 파싱 (JSON 추출)
            # Gemini가 마크다운 코드블록(```json ... ```)으로 감싸서 줄 때가 많음
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            topics = json.loads(text.strip())
            return topics
            
        except Exception as e:
            print(f"Error in NewsCurator: {e}")
            return []

class NewsAnalyst:
    """
    선정된 토픽에 대해 심층 분석 리포트를 작성하는 역할
    """
    def analyze_topic(self, topic_info: Dict, related_news: List[Dict]) -> str:
        # TODO: Implement detailed analysis logic
        pass

class ReportBuilder:
    """
    분석 결과와 나머지 뉴스들을 조합하여 최종 HTML을 생성하는 역할
    """
    def build_html(self, analysis_results: List[Dict], other_news: List[Dict]) -> str:
        # TODO: Implement HTML building logic using Jinja2 or simple string replacement
        pass

# 테스트 코드
if __name__ == "__main__":
    # 가짜 데이터 또는 DB에서 로드하여 테스트
    pass

