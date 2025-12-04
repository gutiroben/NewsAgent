import json
from typing import List, Dict
import google.generativeai as genai
from config import settings

class B2BInsightsAnalyzer:
    """
    선정된 Top5 기사를 기반으로 삼성전자 MX 사업부 B2B 개발그룹 관점의 시사점 분석
    """
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

    def analyze_insights(self, top5_articles: List[Dict]) -> Dict:
        """
        Top5 기사들을 받아 B2B 관점의 시사점을 생성
        """
        if not top5_articles:
            return {
                'key_issues': [],
                'implications': '',
                'action_items': []
            }
        
        # Top5 기사 정보 구성
        input_text = ""
        for idx, article in enumerate(top5_articles):
            title = article.get('title_korean', article['title'])
            summary = article.get('core_summary', '')
            detail = article.get('detailed_explanation', '')
            selection_reason = article.get('selection_reason', '')
            input_text += f"[기사 {idx+1}] {title}\n"
            input_text += f"    선정 이유: {selection_reason}\n"
            input_text += f"    핵심 요약: {summary}\n"
            input_text += f"    상세 설명: {detail}\n\n"

        prompt = f"""
        당신은 삼성전자 MX 사업부 B2B 개발그룹의 전략 분석가입니다.
        아래는 B2B 개발그룹 관점에서 선정된 Top 5 AI 뉴스 기사입니다.
        
        이 5개 기사들을 종합적으로 분석하여:
        1. 주목해야 할 핵심 이슈들 (각 기사별 또는 통합 관점)
        2. 삼성전자 MX 사업부 B2B 개발그룹에 대한 비즈니스/기술적 시사점
        3. 고려해야 할 액션 아이템 또는 전략적 제안
        
        을 정리해주세요.
        
        출력 형식은 반드시 유효한 JSON이어야 합니다:
        {{
            "key_issues": [
                {{
                    "title": "이슈 제목 (한국어)",
                    "description": "이슈 설명 및 왜 중요한지 (한국어, 2-3문장)",
                    "related_article_index": 0  // 관련 기사 번호 (1-5)
                }}
            ],
            "implications": "전체적인 시사점 및 비즈니스/기술적 함의를 종합적으로 설명 (한국어, 5-7문장)",
            "action_items": [
                "액션 아이템 1 (한국어)",
                "액션 아이템 2 (한국어)",
                ...
            ]
        }}
        
        선정된 Top 5 기사:
        {input_text}
        """
        
        try:
            # 전략적 인사이트를 위해 temperature=0.4 설정
            generation_config = {"temperature": 0.4}
            response = self.model.generate_content(prompt, generation_config=generation_config)
            text = response.text
            
            # JSON 추출
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            insights = json.loads(text.strip())
            return insights
            
        except Exception as e:
            print(f"Error in B2B insights analysis: {e}")
            return {
                'key_issues': [],
                'implications': '분석 중 오류가 발생했습니다.',
                'action_items': []
            }



