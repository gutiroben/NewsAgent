import json
import time
import os
import re
from typing import List, Dict, Any
import google.generativeai as genai
from config import settings
from src.collector import TARGET_ARTICLE_TITLE

class NewsAnalyst:
    """
    뉴스를 3개씩 묶어서 심층 분석(Deep Dive)을 수행하는 역할
    """
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

    def _is_target_article(self, title: str) -> bool:
        """타겟 기사인지 확인"""
        return TARGET_ARTICLE_TITLE.lower() in title.lower()
    
    def analyze_batch(self, news_batch: List[Dict]) -> List[Dict]:
        if not news_batch:
            return []

        # 배치에 타겟 기사 포함 여부 확인
        target_in_batch = False
        target_indices = []
        for idx, news in enumerate(news_batch):
            if self._is_target_article(news['title']):
                target_in_batch = True
                target_indices.append(idx)
                print(f"\n[DEBUG] Step 2.1: Target article found in batch!")
                print(f"[DEBUG] Step 2.1: Batch index: {idx}")
                print(f"[DEBUG] Step 2.1: Title: {news['title']}")
                print(f"[DEBUG] Step 2.1: Source: {news.get('source', 'Unknown')}")
                print(f"[DEBUG] Step 2.1: Link: {news.get('link', 'N/A')}")

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
        
        if target_in_batch:
            print(f"[DEBUG] Step 2.2: Sending batch to Gemini API (batch size: {len(news_batch)})")
            print(f"[DEBUG] Step 2.2: Target article indices in batch: {target_indices}")

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
            
            if target_in_batch:
                print(f"[DEBUG] Step 2.3: Calling Gemini API...")
            
            response = self.model.generate_content(prompt, generation_config=generation_config)
            
            text = response.text
            
            if target_in_batch:
                print(f"[DEBUG] Step 2.4: Received response from Gemini API")
                print(f"[DEBUG] Step 2.4: Response length: {len(text)} characters")
                # 원본 응답 저장 (디버깅용)
                os.makedirs('logs', exist_ok=True)
                from datetime import datetime
                from zoneinfo import ZoneInfo
                kst = ZoneInfo("Asia/Seoul")
                timestamp = datetime.now(kst).strftime("%Y%m%d_%H%M%S")
                log_file = f"logs/gemini_response_{timestamp}.txt"
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("=== Gemini API Raw Response ===\n")
                    f.write(text)
                    f.write("\n\n=== Batch Info ===\n")
                    for idx, news in enumerate(news_batch):
                        f.write(f"[{idx}] {news['title']}\n")
                print(f"[DEBUG] Step 2.4: Raw response saved to: {log_file}")
            
            # 마크다운 코드 블록에서 첫 번째 유효한 JSON만 추출
            clean_text = text.strip()
            
            # 여러 JSON 블록이 있는 경우 첫 번째만 사용
            json_blocks = []
            if "```json" in clean_text:
                # ```json ... ``` 블록 찾기
                pattern = r'```json\s*(.*?)\s*```'
                matches = re.findall(pattern, clean_text, re.DOTALL)
                json_blocks = matches
            elif "```" in clean_text:
                # 일반 ``` ... ``` 블록 찾기
                pattern = r'```[^\n]*\s*(.*?)\s*```'
                matches = re.findall(pattern, clean_text, re.DOTALL)
                json_blocks = matches
            
            # 첫 번째 JSON 블록 사용
            if json_blocks:
                clean_text = json_blocks[0].strip()
                if target_in_batch and len(json_blocks) > 1:
                    print(f"[WARNING] Step 2.5: Found {len(json_blocks)} JSON blocks, using first one only")
            else:
                # 마크다운 블록이 없는 경우 기존 로직 사용
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                elif clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                
                clean_text = clean_text.strip()
            
            if target_in_batch:
                print(f"[DEBUG] Step 2.5: Cleaned text length: {len(clean_text)} characters")
            
            # 첫 번째 유효한 JSON 배열만 파싱 시도
            analyzed_list = None
            try:
                analyzed_list = json.loads(clean_text)
                
                if target_in_batch:
                    print(f"[DEBUG] Step 2.6: JSON parsing successful!")
                    print(f"[DEBUG] Step 2.6: Parsed items count: {len(analyzed_list)}")
                    print(f"[DEBUG] Step 2.6: Expected items count: {len(news_batch)}")
                    
            except json.JSONDecodeError as je:
                # 파싱 실패 시 첫 번째 유효한 JSON 배열만 찾아서 파싱 시도
                print(f"[WARNING] Step 2.6: Initial JSON parsing failed: {je}")
                print(f"[WARNING] Step 2.6: Attempting to extract first valid JSON array...")
                
                try:
                    # 첫 번째 '[' 부터 시작하는 JSON 배열 찾기
                    start_idx = clean_text.find('[')
                    if start_idx != -1:
                        # 첫 번째 '[' 부터 시작해서 유효한 JSON 배열 찾기
                        bracket_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(clean_text)):
                            if clean_text[i] == '[':
                                bracket_count += 1
                            elif clean_text[i] == ']':
                                bracket_count -= 1
                                if bracket_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        if end_idx > start_idx:
                            json_candidate = clean_text[start_idx:end_idx]
                            analyzed_list = json.loads(json_candidate)
                            print(f"[DEBUG] Step 2.6: Successfully extracted first valid JSON array!")
                            print(f"[DEBUG] Step 2.6: Parsed items count: {len(analyzed_list)}")
                        else:
                            raise ValueError("Could not find valid JSON array boundaries")
                    else:
                        raise ValueError("No JSON array found in response")
                        
                except Exception as e2:
                    print(f"[ERROR] JSON Parsing Error in Analyst: {je}")
                    print(f"[ERROR] Fallback parsing also failed: {e2}")
                    print(f"[ERROR] Raw Text from Gemini:\n{text[:500]}...")  # 처음 500자만 출력
                    if target_in_batch:
                        print(f"[ERROR] Target article was in this batch - parsing failed!")
                    return news_batch # 파싱 실패 시 원본 반환
            
            if analyzed_list is None:
                print(f"[ERROR] Failed to parse JSON from Gemini response")
                if target_in_batch:
                    print(f"[ERROR] Target article was in this batch - parsing failed!")
                return news_batch

            final_results = []
            processed_indices = set()
            
            for item in analyzed_list:
                idx = item.get('index')
                if idx is not None and 0 <= idx < len(news_batch):
                    combined = news_batch[idx].copy()
                    combined.update(item)
                    final_results.append(combined)
                    processed_indices.add(idx)
                    
                    # 타겟 기사 처리 확인
                    if self._is_target_article(news_batch[idx]['title']):
                        print(f"\n[DEBUG] Step 2.7: Target article processed!")
                        print(f"[DEBUG] Step 2.7: Index: {idx}")
                        print(f"[DEBUG] Step 2.7: Original title: {news_batch[idx]['title']}")
                        print(f"[DEBUG] Step 2.7: title_korean: {item.get('title_korean', 'MISSING')}")
                        print(f"[DEBUG] Step 2.7: core_summary: {bool(item.get('core_summary'))} (length: {len(item.get('core_summary', ''))})")
                        print(f"[DEBUG] Step 2.7: detailed_explanation: {bool(item.get('detailed_explanation'))} (length: {len(item.get('detailed_explanation', ''))})")
            
            # 누락된 기사 확인
            missing_indices = set(range(len(news_batch))) - processed_indices
            if missing_indices:
                print(f"[WARNING] Step 2.8: Some articles were not processed!")
                print(f"[WARNING] Step 2.8: Missing indices: {missing_indices}")
                for missing_idx in missing_indices:
                    print(f"[WARNING] Step 2.8: Missing article [{missing_idx}]: {news_batch[missing_idx]['title']}")
                    if self._is_target_article(news_batch[missing_idx]['title']):
                        print(f"[ERROR] Step 2.8: TARGET ARTICLE WAS NOT PROCESSED!")
            
            if target_in_batch:
                target_found_in_results = any(self._is_target_article(r.get('title', '')) for r in final_results)
                print(f"[DEBUG] Step 2.9: Target article in final_results: {target_found_in_results}")
                if target_found_in_results:
                    for r in final_results:
                        if self._is_target_article(r.get('title', '')):
                            print(f"[DEBUG] Step 2.9: Final result for target:")
                            print(f"[DEBUG] Step 2.9: - title_korean: {r.get('title_korean', 'MISSING')}")
                            print(f"[DEBUG] Step 2.9: - core_summary: {bool(r.get('core_summary'))} ({len(r.get('core_summary', ''))} chars)")
                            print(f"[DEBUG] Step 2.9: - detailed_explanation: {bool(r.get('detailed_explanation'))} ({len(r.get('detailed_explanation', ''))} chars)")
            
            return final_results

        except Exception as e:
            print(f"Error in analyzing batch: {e}")
            return news_batch

    def analyze_all(self, all_news: List[Dict], batch_size=3) -> List[Dict]:
        print(f"Analyzing {len(all_news)} news items in batches of {batch_size}...")
        
        # 타겟 기사가 전체 뉴스 리스트에 있는지 확인
        target_found = False
        target_index = -1
        for idx, news in enumerate(all_news):
            if self._is_target_article(news['title']):
                target_found = True
                target_index = idx
                print(f"\n[DEBUG] Step 2.0: Target article found in all_news!")
                print(f"[DEBUG] Step 2.0: Index: {idx}")
                print(f"[DEBUG] Step 2.0: Title: {news['title']}")
                break
        
        if not target_found:
            print(f"[WARNING] Step 2.0: Target article not found in all_news list!")
        
        results = []
        batch_num = 0
        
        for i in range(0, len(all_news), batch_size):
            batch_num += 1
            batch = all_news[i:i+batch_size]
            batch_start_idx = i
            
            if target_found and target_index >= i and target_index < i + batch_size:
                print(f"\n[DEBUG] Step 2.0: Target article is in batch #{batch_num} (indices {i} to {i+len(batch)-1})")
            
            analyzed_batch = self.analyze_batch(batch)
            
            # 배치 결과 검증
            if len(analyzed_batch) != len(batch):
                print(f"[WARNING] Step 2.0: Batch #{batch_num} result count mismatch!")
                print(f"[WARNING] Step 2.0: Expected: {len(batch)}, Got: {len(analyzed_batch)}")
            
            results.extend(analyzed_batch)
            time.sleep(1) # Rate limit 고려
        
        # 최종 결과에서 타겟 기사 확인
        target_in_results = False
        for idx, result in enumerate(results):
            if self._is_target_article(result.get('title', '')):
                target_in_results = True
                print(f"\n[DEBUG] Step 2.10: Target article found in final results!")
                print(f"[DEBUG] Step 2.10: Result index: {idx}")
                print(f"[DEBUG] Step 2.10: Has title_korean: {bool(result.get('title_korean'))}")
                print(f"[DEBUG] Step 2.10: Has core_summary: {bool(result.get('core_summary'))}")
                print(f"[DEBUG] Step 2.10: Has detailed_explanation: {bool(result.get('detailed_explanation'))}")
                break
        
        if target_found and not target_in_results:
            print(f"[ERROR] Step 2.10: Target article was lost during analysis!")
            
        return results

