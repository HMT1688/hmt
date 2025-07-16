#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 분석 스케줄러
24시간 자동 실행 작업들
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.keyword_gen.generator import keyword_generator
from src.api.naver_api import naver_api
from src.database import (
    insert_keyword, insert_analysis_result, get_db_connection
)

class KeywordScheduler:
    """키워드 분석 스케줄러 클래스"""
    
    def __init__(self):
        self.max_daily_keywords = int(os.getenv("MAX_DAILY_KEYWORDS", 1000))
        self.alert_threshold = int(os.getenv("ALERT_THRESHOLD", 70))
        self.api_delay = 1.0  # API 호출 간 지연 시간
    
    def batch_keyword_generation(self):
        """새벽 1시 - 대량 키워드 생성"""
        print(f"🌙 [{datetime.now().strftime('%H:%M')}] 대량 키워드 생성 시작...")
        
        try:
            # 일일 배치 키워드 생성
            new_keywords = keyword_generator.generate_daily_batch(self.max_daily_keywords)
            
            # 데이터베이스에 저장
            saved_count = 0
            for keyword_data in new_keywords:
                keyword_id = insert_keyword(
                    text=keyword_data["text"],
                    category=keyword_data.get("category", "general"),
                    base_keyword=keyword_data.get("base_keyword"),
                    is_derivative=keyword_data.get("type", "").endswith("_derivative"),
                    priority=self._determine_priority(keyword_data)
                )
                
                if keyword_id:
                    saved_count += 1
            
            print(f"✅ 키워드 생성 완료: {saved_count}개 저장")
            
            # 트렌딩 키워드 기반 파생 생성
            self._generate_trending_derivatives()
            
        except Exception as e:
            print(f"❌ 키워드 생성 중 오류: {e}")
    
    def priority_analysis(self):
        """오전 6시 - 우선순위 키워드 분석"""
        print(f"🌅 [{datetime.now().strftime('%H:%M')}] 우선순위 분석 시작...")
        
        try:
            # 우선순위가 높은 키워드들 조회 (분석되지 않은 것들)
            priority_keywords = self._get_priority_keywords(limit=50)
            
            if not priority_keywords:
                print("📋 분석할 우선순위 키워드가 없습니다.")
                return
            
            analyzed_count = 0
            high_potential_count = 0
            
            for keyword_id, keyword_text in priority_keywords:
                print(f"📊 분석 중: {keyword_text}")
                
                # 네이버 API로 트렌드 분석
                trend_data = naver_api.get_3year_trend(keyword_text)
                
                if trend_data:
                    analysis = naver_api.analyze_trend_pattern(trend_data)
                    
                    if analysis:
                        # 유망도 점수 계산
                        promise_score = self._calculate_promise_score(analysis)
                        analysis["promise_score"] = promise_score
                        
                        # 분석 결과 저장
                        insert_analysis_result(keyword_id, analysis)
                        analyzed_count += 1
                        
                        # 고잠재력 키워드 체크
                        if promise_score >= self.alert_threshold:
                            high_potential_count += 1
                            print(f"🚨 고잠재력 키워드 발견: {keyword_text} (점수: {promise_score})")
                
                # API 제한 방지
                time.sleep(self.api_delay)
            
            print(f"✅ 우선순위 분석 완료: {analyzed_count}개 분석, {high_potential_count}개 고잠재력")
            
        except Exception as e:
            print(f"❌ 우선순위 분석 중 오류: {e}")
    
    def realtime_monitoring(self):
        """매시간 - 실시간 모니터링"""
        print(f"⚡ [{datetime.now().strftime('%H:%M')}] 실시간 모니터링 시작...")
        
        try:
            # 관심 키워드들의 상태 업데이트
            my_keywords = self._get_my_keywords()
            
            for keyword_id, keyword_text in my_keywords:
                # 최신 트렌드 확인
                trend_data = naver_api.get_3year_trend(keyword_text)
                
                if trend_data:
                    analysis = naver_api.analyze_trend_pattern(trend_data)
                    
                    if analysis:
                        # 급상승 감지
                        if analysis.get("acceleration", 0) > 50:
                            print(f"📈 급상승 감지: {keyword_text} (+{analysis['acceleration']:.1f}%)")
                
                time.sleep(self.api_delay)
            
            # 새로운 급상승 키워드 스캔
            self._scan_for_sudden_rises()
            
        except Exception as e:
            print(f"❌ 실시간 모니터링 중 오류: {e}")
    
    def evening_report(self):
        """저녁 8시 - 일일 리포트 및 학습"""
        print(f"🌆 [{datetime.now().strftime('%H:%M')}] 일일 리포트 생성...")
        
        try:
            # 오늘의 통계
            today_stats = self._get_today_stats()
            
            print(f"📊 오늘의 성과:")
            print(f"   분석된 키워드: {today_stats['analyzed']}개")
            print(f"   새로운 발견: {today_stats['discoveries']}개")
            print(f"   고잠재력: {today_stats['high_potential']}개")
            
            # 개인화 모델 업데이트
            self._update_personalization()
            
            # 내일 우선순위 설정
            self._set_tomorrow_priorities()
            
        except Exception as e:
            print(f"❌ 일일 리포트 중 오류: {e}")
    
    def _determine_priority(self, keyword_data: dict) -> int:
        """키워드 우선순위 결정 (1=최고, 4=최저)"""
        
        # 파생 키워드는 높은 우선순위
        if keyword_data.get("type", "").endswith("_derivative"):
            return 1
        
        # 틈새 키워드도 높은 우선순위
        if keyword_data.get("category") == "niche":
            return 2
        
        # 트렌딩 기반은 중간 우선순위
        if "trending" in keyword_data.get("type", ""):
            return 2
        
        # 기본 조합은 낮은 우선순위
        return 3
    
    def _get_priority_keywords(self, limit: int = 50) -> list:
        """우선순위 키워드 조회"""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT k.id, k.text
                FROM keywords k
                LEFT JOIN analysis_results ar ON k.id = ar.keyword_id
                WHERE ar.id IS NULL  -- 아직 분석되지 않은 키워드
                ORDER BY k.priority ASC, k.created_at ASC
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            return results
            
        finally:
            conn.close()
    
    def _get_my_keywords(self) -> list:
        """관심 표시한 키워드들 조회"""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT k.id, k.text
                FROM keywords k
                JOIN user_actions ua ON k.id = ua.keyword_id
                WHERE ua.action = 'liked'
                ORDER BY ua.created_at DESC
                LIMIT 20
            """)
            
            results = cursor.fetchall()
            return results
            
        finally:
            conn.close()
    
    def _calculate_promise_score(self, analysis: dict) -> int:
        """유망도 점수 계산 (100점 만점)"""
        
        score = 0
        
        # 성장률 점수 (40점)
        growth_rate = analysis.get("growth_rate", 0)
        if growth_rate > 100:
            score += 40
        elif growth_rate > 50:
            score += 30
        elif growth_rate > 20:
            score += 20
        elif growth_rate > 0:
            score += 10
        
        # 현재 단계 점수 (30점) - 초기일수록 높음
        stage = analysis.get("stage", "mature")
        if stage == "embryo":
            score += 30
        elif stage == "early":
            score += 20
        elif stage == "growth":
            score += 10
        
        # 최근 가속화 점수 (30점)
        acceleration = analysis.get("acceleration", 0)
        if acceleration > 100:
            score += 30
        elif acceleration > 50:
            score += 20
        elif acceleration > 20:
            score += 10
        
        return min(score, 100)
    
    def _generate_trending_derivatives(self):
        """트렌딩 키워드 기반 파생 생성"""
        
        # 최근 7일간 고점수 키워드들 조회
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT k.text, ar.promise_score
                FROM keywords k
                JOIN analysis_results ar ON k.id = ar.keyword_id
                WHERE ar.analyzed_at >= date('now', '-7 days')
                AND ar.promise_score >= ?
                AND k.is_derivative = 0  -- 기본 키워드만
                ORDER BY ar.promise_score DESC
                LIMIT 5
            """, (80,))
            
            trending_keywords = cursor.fetchall()
            
            for keyword_text, score in trending_keywords:
                print(f"🔥 트렌딩 키워드 발견: {keyword_text} (점수: {score})")
                
                # 파생 키워드 생성
                derivatives = keyword_generator.generate_derivative_keywords(keyword_text, 20)
                
                # 데이터베이스에 저장 (높은 우선순위)
                for derivative in derivatives:
                    insert_keyword(
                        text=derivative["text"],
                        category="derivative",
                        base_keyword=keyword_text,
                        is_derivative=True,
                        priority=1  # 최고 우선순위
                    )
                
                # 트렌딩 키워드 목록에 추가
                keyword_generator.add_trending_keyword(keyword_text)
        
        finally:
            conn.close()
    
    def _scan_for_sudden_rises(self):
        """급상승 키워드 스캔"""
        
        # 최근 분석된 키워드 중 급상승하는 것들 찾기
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT k.text, ar.acceleration, ar.promise_score
                FROM keywords k
                JOIN analysis_results ar ON k.id = ar.keyword_id
                WHERE ar.analyzed_at >= date('now', '-1 days')
                AND ar.acceleration > 50
                ORDER BY ar.acceleration DESC
                LIMIT 10
            """)
            
            sudden_rises = cursor.fetchall()
            
            for keyword_text, acceleration, score in sudden_rises:
                print(f"⚡ 급상승: {keyword_text} (+{acceleration:.1f}%, 점수: {score})")
        
        finally:
            conn.close()
    
    def _get_today_stats(self) -> dict:
        """오늘의 통계 조회"""
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 오늘 분석된 키워드 수
            cursor.execute("""
                SELECT COUNT(*) FROM analysis_results 
                WHERE date(analyzed_at) = date('now')
            """)
            analyzed = cursor.fetchone()[0]
            
            # 오늘 생성된 키워드 수
            cursor.execute("""
                SELECT COUNT(*) FROM keywords 
                WHERE date(created_at) = date('now')
            """)
            discoveries = cursor.fetchone()[0]
            
            # 고잠재력 키워드 수
            cursor.execute("""
                SELECT COUNT(*) FROM analysis_results 
                WHERE date(analyzed_at) = date('now')
                AND promise_score >= ?
            """, (self.alert_threshold,))
            high_potential = cursor.fetchone()[0]
            
            return {
                "analyzed": analyzed,
                "discoveries": discoveries,
                "high_potential": high_potential
            }
        
        finally:
            conn.close()
    
    def _update_personalization(self):
        """개인화 모델 업데이트"""
        
        # 사용자 액션 패턴 분석
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 좋아한 키워드들의 패턴 분석
            cursor.execute("""
                SELECT k.category, k.text, ar.growth_rate, ar.stage
                FROM keywords k
                JOIN user_actions ua ON k.id = ua.keyword_id
                JOIN analysis_results ar ON k.id = ar.keyword_id
                WHERE ua.action = 'liked'
                ORDER BY ua.created_at DESC
                LIMIT 50
            """)
            
            liked_patterns = cursor.fetchall()
            
            # 패턴 분석 (간단한 버전)
            categories = {}
            for category, text, growth_rate, stage in liked_patterns:
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
            
            print(f"📈 선호 카테고리: {categories}")
        
        finally:
            conn.close()
    
    def _set_tomorrow_priorities(self):
        """내일 우선순위 설정"""
        
        # 분석되지 않은 키워드들의 우선순위 재조정
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 파생 키워드들을 최우선으로
            cursor.execute("""
                UPDATE keywords 
                SET priority = 1
                WHERE is_derivative = 1 
                AND id NOT IN (
                    SELECT keyword_id FROM analysis_results
                )
            """)
            
            conn.commit()
            print("✅ 내일 우선순위 설정 완료")
        
        finally:
            conn.close()

# 전역 인스턴스
keyword_scheduler = KeywordScheduler()

# 수동 실행 함수들
def run_batch_generation():
    """수동으로 배치 생성 실행"""
    keyword_scheduler.batch_keyword_generation()

def run_priority_analysis():
    """수동으로 우선순위 분석 실행"""
    keyword_scheduler.priority_analysis()

def run_realtime_monitoring():
    """수동으로 실시간 모니터링 실행"""
    keyword_scheduler.realtime_monitoring()

if __name__ == "__main__":
    # 테스트 실행
    print("🧪 스케줄러 테스트 시작...")
    
    # 소량 키워드 생성 테스트
    print("\n1. 키워드 생성 테스트:")
    keyword_scheduler.max_daily_keywords = 10  # 테스트용으로 줄임
    keyword_scheduler.batch_keyword_generation()
    
    # 우선순위 분석 테스트 (1개만)
    print("\n2. 우선순위 분석 테스트:")
    priority_keywords = keyword_scheduler._get_priority_keywords(1)
    if priority_keywords:
        keyword_id, keyword_text = priority_keywords[0]
        print(f"테스트 분석: {keyword_text}")
        # 실제 API 호출은 생략 (테스트용)
    
    print("\n✅ 스케줄러 테스트 완료!")