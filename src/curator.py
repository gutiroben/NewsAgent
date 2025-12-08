import json
from typing import List, Dict
import google.generativeai as genai
from config import settings
from src.collector import TARGET_ARTICLE_TITLE

class NewsCurator:
    """
    분석된 뉴스 전체를 보고 Top N 기사를 선정하는 역할
    """
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

    def _is_target_article(self, title: str) -> bool:
        """타겟 기사인지 확인"""
        return TARGET_ARTICLE_TITLE.lower() in title.lower()
    
    def select_top_articles(self, analyzed_news: List[Dict]) -> List[Dict]:
        """
        분석된 뉴스 리스트를 받아 Top 5 기사 선정
        삼성전자 MX 사업부 B2B 개발그룹 관점에서 주목할 만한 기사 선정
        """
        if not analyzed_news:
            return []
        
        # 타겟 기사 확인
        target_found = False
        target_index = -1
        for idx, news in enumerate(analyzed_news):
            title = news.get('title', '')
            if self._is_target_article(title):
                target_found = True
                target_index = idx
                print(f"\n[DEBUG] Step 3.1: Target article found in analyzed_news!")
                print(f"[DEBUG] Step 3.1: Index: {idx}")
                print(f"[DEBUG] Step 3.1: Original title: {title}")
                print(f"[DEBUG] Step 3.1: title_korean: {news.get('title_korean', 'MISSING')}")
                print(f"[DEBUG] Step 3.1: core_summary: {bool(news.get('core_summary'))} ({len(news.get('core_summary', ''))} chars)")
                print(f"[DEBUG] Step 3.1: detailed_explanation: {bool(news.get('detailed_explanation'))} ({len(news.get('detailed_explanation', ''))} chars)")
                break
        
        if not target_found:
            print(f"[WARNING] Step 3.1: Target article not found in analyzed_news!")
            
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
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            selected_list = json.loads(text.strip())
            
            if target_found:
                print(f"[DEBUG] Step 3.2: Selected articles count: {len(selected_list)}")
                target_selected = False
                for item in selected_list:
                    if item.get('article_index') == target_index:
                        target_selected = True
                        print(f"[DEBUG] Step 3.2: Target article was selected!")
                        break
                if not target_selected:
                    print(f"[DEBUG] Step 3.2: Target article was NOT selected")
            
            # 결과 매핑: 선정된 기사 정보를 찾아서 리스트로 반환
            final_top5 = []
            for item in selected_list:
                idx = item.get('article_index')
                if idx is not None and 0 <= idx < len(analyzed_news):
                    article = analyzed_news[idx].copy()
                    article['selection_reason'] = item.get('selection_reason')
                    final_top5.append(article)
                    
                    if target_found and idx == target_index:
                        print(f"[DEBUG] Step 3.3: Target article added to top5!")
                        print(f"[DEBUG] Step 3.3: title_korean: {article.get('title_korean', 'MISSING')}")
                        print(f"[DEBUG] Step 3.3: core_summary: {bool(article.get('core_summary'))}")
                        print(f"[DEBUG] Step 3.3: detailed_explanation: {bool(article.get('detailed_explanation'))}")
                    
            return final_top5
            
        except Exception as e:
            print(f"Error in curator: {e}")
            return []

