import time
from typing import List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import google.generativeai as genai
from config import settings
from src.utils.json_parser import parse_json

class NewsAnalyst:
    """
    뉴스를 하나씩 심층 분석(Deep Dive)을 수행하는 역할
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
            
            # JSON 파싱 (공통 파서 사용)
            batch_num = getattr(self, '_current_batch_num', 0)
            context = f"analyst_batch_{batch_num}"
            
            try:
                analyzed_list = parse_json(text, context=context)
            except Exception as e:
                print(f"[ERROR] JSON Parsing Error in Analyst: {e}")
                return news_batch  # 파싱 실패 시 원본 반환

            final_results = []
            processed_indices = set()
            
            for item in analyzed_list:
                idx = item.get('index')
                if idx is not None and 0 <= idx < len(news_batch):
                    combined = news_batch[idx].copy()
                    combined.update(item)
                    final_results.append(combined)
                    processed_indices.add(idx)
            
            # 누락된 기사 확인
            missing_indices = set(range(len(news_batch))) - processed_indices
            if missing_indices:
                print(f"[WARNING] Step 2.8: Some articles were not processed!")
                print(f"[WARNING] Step 2.8: Missing indices: {missing_indices}")
                for missing_idx in missing_indices:
                    print(f"[WARNING] Step 2.8: Missing article [{missing_idx}]: {news_batch[missing_idx]['title']}")
            
            return final_results

        except Exception as e:
            print(f"Error in analyzing batch: {e}")
            return news_batch

    def analyze_all(self, all_news: List[Dict], batch_size=1) -> List[Dict]:
        """
        모든 뉴스를 배치 단위로 분석 (배치 크기 1 = 개별 처리)
        
        Args:
            all_news: 분석할 뉴스 리스트
            batch_size: 배치 크기 (기본값 1 = 개별 처리)
            
        Returns:
            분석 결과 리스트
        """
        print(f"Analyzing {len(all_news)} news items in batches of {batch_size}...")
        
        results = []
        batch_num = 0
        
        for i in range(0, len(all_news), batch_size):
            batch_num += 1
            batch = all_news[i:i+batch_size]
            
            # batch_num을 analyze_batch에서 사용할 수 있도록 설정
            self._current_batch_num = batch_num
            
            print(f"Processing batch {batch_num} ({len(batch)} article(s))...")
            
            analyzed_batch = self.analyze_batch(batch)
            
            # 배치 결과 검증
            if len(analyzed_batch) != len(batch):
                print(f"[WARNING] Step 2.0: Batch #{batch_num} result count mismatch!")
                print(f"[WARNING] Step 2.0: Expected: {len(batch)}, Got: {len(analyzed_batch)}")
            
            results.extend(analyzed_batch)
            time.sleep(1)  # Rate limit 고려
        
        return results

