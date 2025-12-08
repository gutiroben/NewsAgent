"""
JSON 파싱 유틸리티 - JSON5 파서 사용 및 오류 로깅
"""
import json
import json5
import re
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any


def parse_json(text: str, context: str = "unknown") -> Any:
    """
    JSON 파싱 (마크다운 제거 + 제어 문자 제거 + JSON5 파싱 + 검증)
    
    Args:
        text: 파싱할 JSON 문자열 (마크다운 코드 블록 포함 가능)
        context: 컨텍스트 정보 (디버깅용, 예: "analyst_batch_1", "curator", "b2b_insights")
    
    Returns:
        파싱된 객체 (dict 또는 list)
    
    Raises:
        json.JSONDecodeError: 파싱 실패 시
    """
    clean_text = text.strip()
    
    # 1. 마크다운 코드 블록에서 JSON 추출
    clean_text = _extract_json_from_markdown(clean_text)
    
    # 2. 제어 문자 제거
    clean_text = _remove_control_characters(clean_text)
    
    try:
        parsed = json5.loads(clean_text)
        # Strict JSON으로 재직렬화하여 검증
        json.dumps(parsed, ensure_ascii=False)
        return parsed
    except (json.JSONDecodeError, ValueError) as e:
        _save_parse_error_log(text, clean_text, e, context)
        raise


def _extract_json_from_markdown(text: str) -> str:
    """마크다운 코드 블록에서 JSON 추출"""
    text = text.strip()
    
    # 여러 JSON 블록이 있는 경우 첫 번째만 사용
    json_blocks = []
    if "```json" in text:
        # ```json ... ``` 블록 찾기
        pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(pattern, text, re.DOTALL)
        json_blocks = matches
    elif "```" in text:
        # 일반 ``` ... ``` 블록 찾기
        pattern = r'```[^\n]*\s*(.*?)\s*```'
        matches = re.findall(pattern, text, re.DOTALL)
        json_blocks = matches
    
    if json_blocks:
        return json_blocks[0].strip()
    
    # 마크다운 블록이 없는 경우 (순수 JSON)
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    
    return text.strip()


def _remove_control_characters(text: str) -> str:
    """제어 문자 제거 (블랙리스트 방식)"""
    # 허용되는 제어 문자: \t (0x09), \n (0x0A), \r (0x0D)
    # 나머지 제어 문자(0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F, BOM) 제거
    return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\uFEFF]', '', text)


def _save_parse_error_log(original_text: str, cleaned_text: str, error: Exception, context: str):
    """JSON 파싱 오류 상세 로그 저장"""
    os.makedirs('logs', exist_ok=True)
    kst = ZoneInfo("Asia/Seoul")
    timestamp = datetime.now(kst).strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/json_parse_error_{timestamp}_{context}.txt"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"=== JSON Parse Error Log ===\n")
        f.write(f"Context: {context}\n")
        f.write(f"Timestamp: {datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S KST')}\n")
        f.write(f"Error Type: {type(error).__name__}\n")
        f.write(f"Error Message: {str(error)}\n")
        f.write(f"\n=== Original Text (first 2000 chars) ===\n")
        f.write(original_text[:2000])
        f.write(f"\n\n=== Cleaned Text (first 2000 chars) ===\n")
        f.write(cleaned_text[:2000])
        f.write(f"\n\n=== Error Details ===\n")
        
        if hasattr(error, 'pos'):
            f.write(f"Error Position: {error.pos}\n")
        if hasattr(error, 'lineno'):
            f.write(f"Error Line: {error.lineno}\n")
        if hasattr(error, 'colno'):
            f.write(f"Error Column: {error.colno}\n")
        
        # 오류 위치 주변 텍스트 표시
        if hasattr(error, 'pos') and error.pos is not None:
            pos = error.pos
            start = max(0, pos - 200)
            end = min(len(cleaned_text), pos + 200)
            f.write(f"\n=== Error Context (char {start}-{end}) ===\n")
            f.write(cleaned_text[start:end])
            f.write(f"\n{' ' * (pos - start)}^\n")
            f.write(f"Error at position {pos}\n")
        
        # 라인별 분석
        if hasattr(error, 'lineno') and error.lineno is not None:
            lines = cleaned_text.split('\n')
            if 0 <= error.lineno - 1 < len(lines):
                error_line = lines[error.lineno - 1]
                f.write(f"\n=== Error Line ({error.lineno}) ===\n")
                f.write(error_line)
                if hasattr(error, 'colno') and error.colno is not None:
                    f.write(f"\n{' ' * (error.colno - 1)}^\n")
    
    print(f"[ERROR] JSON parse error logged to: {log_file}")

