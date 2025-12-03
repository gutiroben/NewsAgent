import os
import requests

def ensure_korean_font():
    """
    나눔고딕 폰트가 있는지 확인하고 없으면 다운로드
    """
    font_dir = "assets/fonts"
    font_path = os.path.join(font_dir, "NanumGothic.ttf")
    
    if os.path.exists(font_path):
        return font_path
        
    print("Downloading NanumGothic font...")
    os.makedirs(font_dir, exist_ok=True)
    
    # Google Fonts CDN (또는 안정적인 소스)
    url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        with open(font_path, "wb") as f:
            f.write(response.content)
            
        print("Font downloaded successfully.")
        return font_path
    except Exception as e:
        print(f"Failed to download font: {e}")
        # 폰트 다운로드 실패 시 None 반환 -> PDF 생성 시 기본 폰트(영어만 나옴) 사용 혹은 에러 처리
        return None

