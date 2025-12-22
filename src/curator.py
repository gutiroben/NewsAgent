from typing import List, Dict
import google.generativeai as genai
from config import settings
from src.utils.json_parser import parse_json

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
        삼성전자 MX 사업부 B2B 개발그룹 관점에서 주목할 만한 기사 선정
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
        당신은 삼성전자 MX 사업부 B2B 개발그룹의 전략 분석가입니다.
        아래는 오늘 수집된 AI 관련 뉴스들의 분석 결과입니다.
        
        **삼성전자 MX 사업부 B2B 개발그룹 관점에서 주목해야 할 Top 5 기사**를 선정해주세요.
        B2B 비즈니스, 엔터프라이즈 솔루션, 개발자 도구, 기업용 AI 서비스 등과 관련된 이슈를 우선적으로 고려하세요.
        단, 일반적인 AI 트렌드도 중요하다면 포함할 수 있습니다.
        
        반드시 5개의 구체적인 기사를 선택하세요. 그룹화하지 마세요.
        
        출력 형식은 반드시 유효한 JSON 리스트여야 합니다:
        [
            {{
                "article_index": 0,  // Integer
                "selection_reason": "B2B 개발그룹 관점에서 왜 이 기사가 중요한지 설명 (한국어, 2-3문장)"
            }},
            ...
        ]
        
        뉴스 목록:
        {input_text}
        """
        
        try:
            # 선정 기준의 일관성을 위해 temperature=0.3 설정
            generation_config = {"temperature": 0.3}
            response = self.model.generate_content(prompt, generation_config=generation_config)
            text = response.text
            
            # JSON 파싱 (공통 파서 사용)
            selected_list = parse_json(text, context="curator")
            
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

