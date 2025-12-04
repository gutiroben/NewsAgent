from typing import List, Dict

class ReportBuilder:
    """
    최종 HTML 이메일 본문을 생성하는 역할
    """
    def build_html(self, top5_articles: List[Dict], all_news: List[Dict], b2b_insights: Dict = None) -> str:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        # 한국 시간대 명시적 사용
        kst = ZoneInfo("Asia/Seoul")
        today_str = datetime.now(kst).strftime("%Y. %m. %d (%a)")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f6f8; }}
                .container {{ max-width: 700px; margin: 0 auto; background: #ffffff; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                .header {{ background: linear-gradient(135deg, #1a2980 0%, #26d0ce 100%); padding: 40px 30px; text-align: center; color: white; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }}
                .header p {{ margin: 10px 0 0; opacity: 0.9; font-size: 15px; }}
                .date-badge {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 13px; margin-bottom: 15px; }}
                .content {{ padding: 30px; }}
                .section-title {{ display: flex; align-items: center; margin: 40px 0 20px; font-size: 20px; font-weight: 700; color: #1a202c; border-bottom: 2px solid #1a202c; padding-bottom: 10px; }}
                
                .topic-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
                .topic-header {{ margin-bottom: 15px; border-bottom: 1px dashed #cbd5e0; padding-bottom: 15px; }}
                .topic-tag {{ display: inline-block; background: #ebf8ff; color: #2b6cb0; font-size: 12px; font-weight: bold; padding: 4px 8px; border-radius: 4px; margin-bottom: 8px; }}
                .topic-title {{ font-size: 20px; color: #2d3748; margin: 0 0 5px 0; font-weight: 700; line-height: 1.3; text-decoration: none; display: block; }}
                .topic-meta {{ font-size: 12px; color: #718096; margin-bottom: 10px; }}
                .topic-summary {{ font-size: 14px; color: #4a5568; line-height: 1.6; margin-bottom: 15px; background-color: #f7fafc; padding: 12px; border-radius: 8px; border-left: 4px solid #4299e1; }}
                
                .pdf-notice {{ margin-top: 40px; padding: 25px; background-color: #edf2f7; border-radius: 12px; text-align: center; border: 2px dashed #cbd5e0; }}
                .footer {{ background: #2d3748; color: #a0aec0; text-align: center; padding: 30px; font-size: 13px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="date-badge">{today_str}</div>
                    <h1>NewsAgent Daily Brief</h1>
                    <p>오늘의 AI 트렌드 & 심층 분석 리포트</p>
                </div>
                
                <div class="content">
        """
        
        # B2B Insights 섹션 추가 (Top5보다 먼저)
        if b2b_insights and (b2b_insights.get('key_issues') or b2b_insights.get('implications')):
            html += """
                    <div class="section-title">
                        <span>💼</span> 삼성전자 MX 사업부 B2B 개발그룹 관점
                    </div>
            """
            
            # Key Issues
            if b2b_insights.get('key_issues'):
                html += '<div style="margin-bottom: 30px;">'
                html += '<h3 style="color: #1a2980; font-size: 16px; margin-bottom: 15px;">🔍 주목할 핵심 이슈</h3>'
                for issue in b2b_insights['key_issues']:
                    html += f"""
                    <div class="topic-card" style="background: #f0f9ff; border-left: 4px solid #1a2980;">
                        <h4 style="margin: 0 0 10px 0; color: #1a2980; font-size: 15px;">{issue.get('title', '')}</h4>
                        <p style="margin: 0; color: #4a5568; font-size: 14px; line-height: 1.6;">{issue.get('description', '')}</p>
                    </div>
                    """
                html += '</div>'
            
            # Implications
            if b2b_insights.get('implications'):
                html += f"""
                <div class="topic-card" style="background: #fff7ed; border-left: 4px solid #f59e0b;">
                    <h3 style="color: #f59e0b; font-size: 16px; margin-bottom: 15px;">💡 비즈니스/기술적 시사점</h3>
                    <p style="margin: 0; color: #4a5568; font-size: 14px; line-height: 1.8;">{b2b_insights['implications']}</p>
                </div>
                """
            
            # Action Items
            if b2b_insights.get('action_items'):
                html += '<div style="margin-top: 30px; margin-bottom: 30px;">'
                html += '<h3 style="color: #1a2980; font-size: 16px; margin-bottom: 15px;">📋 고려사항</h3>'
                html += '<ul style="margin: 0; padding-left: 20px; color: #4a5568; font-size: 14px; line-height: 1.8;">'
                for item in b2b_insights['action_items']:
                    html += f'<li>{item}</li>'
                html += '</ul></div>'
            
            html += '<hr style="margin: 40px 0; border: none; border-top: 2px solid #e2e8f0;">'
        
        # 기존 Top5 섹션
        html += """
                    <div class="section-title">
                        <span>🔥</span> Today's Top 5 Deep Dive
                    </div>
        """
        
        
        for idx, article in enumerate(top5_articles):
            title = article.get('title_korean', article['title'])
            summary = article.get('core_summary', '')
            selection_reason = article.get('selection_reason', '')
            source = article.get('source', '')
            link = article.get('link', '')
            
            reason_html = ""
            if selection_reason:
                reason_html = f'<div style="margin-bottom: 10px; color: #e53e3e; font-weight: bold; font-size: 13px;">💡 선정 이유: {selection_reason}</div>'

            html += f"""
            <div class="topic-card">
                <div class="topic-header">
                    <span class="topic-tag">TOPIC {idx+1:02d}</span>
                    {reason_html}
                    <a href="{link}" class="topic-title" target="_blank">{title}</a>
                    <div class="topic-meta">{source} | {article.get('published_at', '')[:10]}</div>
                </div>
                
                <div class="topic-summary">
                    <b>[핵심 요지]</b><br>{summary}
                </div>
                
                <div style="text-align: right; margin-top: 15px;">
                    <a href="{link}" style="color: #3182ce; text-decoration: none; font-size: 14px; font-weight: bold;">원문 전체 읽기 →</a>
                </div>
            </div>
            """

        html += f"""
            <div class="pdf-notice">
                <h3>📥 전체 리포트 (PDF) 확인하기</h3>
                <p style="margin: 0; color: #4a5568; font-size: 14px; line-height: 1.6;">
                    총 {len(all_news)}개의 AI 뉴스에 대한<br>
                    <strong>심층 분석(Deep Dive)과 전체 목록</strong>은<br>
                    함께 첨부된 <strong>PDF 파일</strong>을 확인해주세요.
                </p>
            </div>
        """

        html += """
                </div>
                <div class="footer">
                    Generated by <strong>NewsAgent</strong> with Gemini 2.5 Flash<br>
                    &copy; 2025 NewsAgent
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

