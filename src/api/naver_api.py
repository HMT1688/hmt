#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 데이터랩 API - 실제 3년 트렌드 분석
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# 환경 변수 로드
load_dotenv()

class NaverTrendAPI:
    """네이버 데이터랩 API 클래스"""
    
    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.base_url = "https://openapi.naver.com/v1/datalab/search"
        
        if not self.client_id or not self.client_secret:
            raise ValueError("네이버 API 키가 설정되지 않았습니다.")
    
    def get_3year_trend_data(self, keyword):
        """3년간 트렌드 데이터 수집"""
        try:
            # 3년 전부터 현재까지 날짜 계산
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3*365)  # 3년 전
            
            # 날짜 포맷팅 (YYYY-MM-DD)
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # API 요청 데이터
            request_data = {
                "startDate": start_date_str,
                "endDate": end_date_str,
                "timeUnit": "week",  # 주 단위로 데이터 수집
                "keywordGroups": [
                    {
                        "groupName": keyword,
                        "keywords": [keyword]
                    }
                ]
            }
            
            # API 호출
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(request_data)
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_trend_data(data, keyword)
            else:
                print(f"❌ API 오류 ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 트렌드 데이터 수집 오류: {e}")
            return None
    
    def _parse_trend_data(self, raw_data, keyword):
        """API 응답 데이터 파싱"""
        try:
            if not raw_data.get("results"):
                return None
            
            # 주간 데이터 추출
            weekly_data = raw_data["results"][0]["data"]
            
            # 데이터 점들을 연도별로 분류
            year1_data = []  # 3년 전
            year2_data = []  # 2년 전  
            year3_data = []  # 1년 전
            
            total_weeks = len(weekly_data)
            weeks_per_year = total_weeks // 3
            
            for i, point in enumerate(weekly_data):
                if i < weeks_per_year:
                    year1_data.append(point["ratio"])
                elif i < weeks_per_year * 2:
                    year2_data.append(point["ratio"])
                else:
                    year3_data.append(point["ratio"])
            
            return {
                "keyword": keyword,
                "year1_data": year1_data,  # 가장 오래된 년도
                "year2_data": year2_data,  # 중간 년도
                "year3_data": year3_data,  # 최근 년도
                "total_weeks": total_weeks,
                "raw_data": weekly_data
            }
            
        except Exception as e:
            print(f"❌ 데이터 파싱 오류: {e}")
            return None
    
    def analyze_keyword_trend(self, keyword):
        """키워드 트렌드 종합 분석 - 핵심 기능!"""
        try:
            print(f"📊 '{keyword}' 3년 트렌드 분석 중...")
            
            # 1. 3년 트렌드 데이터 수집
            trend_data = self.get_3year_trend_data(keyword)
            if not trend_data:
                return {"success": False, "error": "데이터 수집 실패"}
            
            # 2. 기본 통계 계산
            year1_avg = sum(trend_data["year1_data"]) / len(trend_data["year1_data"])
            year2_avg = sum(trend_data["year2_data"]) / len(trend_data["year2_data"])
            year3_avg = sum(trend_data["year3_data"]) / len(trend_data["year3_data"])
            
            # 3. 성장률 계산 (년도별)
            growth_rate_y1_y2 = ((year2_avg - year1_avg) / year1_avg * 100) if year1_avg > 0 else 0
            growth_rate_y2_y3 = ((year3_avg - year2_avg) / year2_avg * 100) if year2_avg > 0 else 0
            overall_growth = ((year3_avg - year1_avg) / year1_avg * 100) if year1_avg > 0 else 0
            
            # 4. 가속화 지수 계산 (핵심!)
            acceleration = growth_rate_y2_y3 - growth_rate_y1_y2
            
            # 5. 계절성 분석
            seasonality = self._analyze_seasonality(trend_data["raw_data"])
            
            # 6. 성장 단계 판별
            stage = self._determine_growth_stage(overall_growth, acceleration, year3_avg)
            
            # 7. "발비닐" 레벨 기회 점수 계산
            opportunity_score = self._calculate_opportunity_score(
                overall_growth, acceleration, seasonality, year3_avg
            )
            
            # 8. 종합 결과
            result = {
                "success": True,
                "keyword": keyword,
                "growth_rate": round(overall_growth, 2),
                "acceleration": round(acceleration, 2),
                "is_seasonal": seasonality["is_seasonal"],
                "seasonality_score": seasonality["score"],
                "stage": stage,
                "opportunity_score": opportunity_score,
                "priority_score": min(100, max(0, int(50 + overall_growth * 0.5 + acceleration * 0.3))),
                "year_averages": {
                    "year1": round(year1_avg, 2),
                    "year2": round(year2_avg, 2), 
                    "year3": round(year3_avg, 2)
                },
                "total_weeks": trend_data["total_weeks"],
                "analysis_time": datetime.now().isoformat()
            }
            
            print(f"✅ 분석 완료: 성장률 {overall_growth:.1f}%, 가속화 {acceleration:.1f}%, 기회점수 {opportunity_score}")
            
            return result
            
        except Exception as e:
            print(f"❌ 키워드 분석 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_seasonality(self, weekly_data):
        """계절성 분석 - 여름/겨울 패턴 감지"""
        try:
            # 52주를 4분기로 나누기
            quarter_size = len(weekly_data) // 4
            quarters = []
            
            for i in range(4):
                start_idx = i * quarter_size
                end_idx = start_idx + quarter_size
                quarter_avg = sum(point["ratio"] for point in weekly_data[start_idx:end_idx]) / quarter_size
                quarters.append(quarter_avg)
            
            # 계절별 편차 계산
            max_quarter = max(quarters)
            min_quarter = min(quarters)
            seasonality_variance = (max_quarter - min_quarter) / max_quarter * 100 if max_quarter > 0 else 0
            
            # 계절성 판별 (편차가 30% 이상이면 계절성 있음)
            is_seasonal = seasonality_variance > 30
            
            return {
                "is_seasonal": is_seasonal,
                "score": round(seasonality_variance, 2),
                "quarters": quarters
            }
            
        except Exception as e:
            print(f"❌ 계절성 분석 오류: {e}")
            return {"is_seasonal": False, "score": 0, "quarters": []}
    
    def _determine_growth_stage(self, growth_rate, acceleration, current_level):
        """성장 단계 판별"""
        if current_level < 10:
            return "dormant"  # 휴면기
        elif growth_rate < 0:
            return "decline"  # 하락기
        elif growth_rate < 20:
            return "stable"   # 안정기
        elif acceleration > 0 and growth_rate > 50:
            return "explosive"  # 폭발적 성장 - "발비닐" 타이밍!
        elif growth_rate > 20:
            return "growth"   # 성장기
        else:
            return "stable"
    
    def _calculate_opportunity_score(self, growth_rate, acceleration, seasonality, current_level):
        """기회 점수 계산 - "발비닐" 발굴용"""
        
        base_score = 0
        
        # 성장률 점수 (0-40점)
        if growth_rate > 100:
            base_score += 40
        elif growth_rate > 50:
            base_score += 30
        elif growth_rate > 20:
            base_score += 20
        elif growth_rate > 0:
            base_score += 10
        
        # 가속화 점수 (0-30점)
        if acceleration > 50:
            base_score += 30
        elif acceleration > 20:
            base_score += 20
        elif acceleration > 0:
            base_score += 10
        
        # 현재 레벨 점수 (0-20점) - 너무 높으면 이미 늦음
        if 10 <= current_level <= 30:
            base_score += 20  # 적당한 레벨
        elif 30 < current_level <= 50:
            base_score += 15
        elif 5 <= current_level < 10:
            base_score += 10  # 아직 너무 낮음
        
        # 계절성 보너스 (0-10점)
        if not seasonality["is_seasonal"]:
            base_score += 10  # 계절성 없으면 더 안정적
        
        return min(100, base_score)
    
    def batch_analyze_keywords(self, keywords, delay=1):
        """여러 키워드 일괄 분석"""
        results = []
        
        for keyword in keywords:
            try:
                result = self.analyze_keyword_trend(keyword)
                results.append(result)
                
                # API 제한 고려하여 딜레이
                time.sleep(delay)
                
            except Exception as e:
                print(f"❌ {keyword} 분석 실패: {e}")
                results.append({
                    "success": False,
                    "keyword": keyword,
                    "error": str(e)
                })
        
        return results

# 전역 인스턴스
naver_api = NaverTrendAPI()

# 테스트 함수
def test_naver_api():
    """네이버 API 테스트"""
    print("🧪 네이버 API 테스트 시작...")
    
    test_keyword = "보냉백"
    result = naver_api.analyze_keyword_trend(test_keyword)
    
    if result.get("success"):
        print(f"✅ API 테스트 성공!")
        print(f"📈 분석 결과: {result}")
    else:
        print(f"❌ API 테스트 실패: {result.get('error')}")

if __name__ == "__main__":
    test_naver_api()