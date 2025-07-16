#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 자동 생성 엔진 - 간단 버전
"""

import random
from typing import List, Dict

class KeywordGenerator:
    """키워드 자동 생성 클래스"""
    
    def __init__(self):
        # 기본 카테고리와 아이템들
        self.base_categories = {
            "뷰티": ["크림", "세럼", "토너", "마스크", "립스틱", "파운데이션"],
            "헬스": ["덤벨", "요가매트", "마사지기", "베개", "쿠션", "패드"],
            "라이프": ["청소기", "정리함", "도마", "팬", "수납함", "매트"],
            "테크": ["케이스", "충전기", "스탠드", "홀더", "필름", "마우스"],
            "아웃도어": ["텐트", "배낭", "의자", "랜턴", "쿨러", "보냉백"]
        }
        
        # 수식어들
        self.modifiers = {
            "타겟": ["1인가구", "직장인", "학생", "시니어"],
            "크기": ["미니", "소형", "휴대용", "컴팩트"],
            "특성": ["무선", "스마트", "자동", "친환경"],
            "용도": ["여행용", "사무실", "차량", "운동"],
            "소재": ["실리콘", "스테인리스", "세라믹"]
        }
        
        # 트렌딩 키워드들
        self.trending_keywords = [
            "보냉백", "목베개", "발매트", "손목패드", "무릎쿠션",
            "미니가습기", "USB워머", "목보호"
        ]
    
    def generate_basic_combinations(self, max_count: int = 100) -> List[Dict]:
        """기본 조합 키워드 생성"""
        
        keywords = []
        
        for category, items in self.base_categories.items():
            for item in items:
                for modifier_type, modifiers in self.modifiers.items():
                    for modifier in modifiers:
                        if len(keywords) >= max_count:
                            return keywords
                        
                        keywords.append({
                            "text": f"{modifier} {item}",
                            "category": category,
                            "type": "basic_combination",
                            "base_item": item,
                            "modifier": modifier
                        })
        
        return keywords[:max_count]
    
    def generate_derivative_keywords(self, base_keyword: str, max_count: int = 20) -> List[Dict]:
        """파생 키워드 생성 (핵심 기능!)"""
        
        derivatives = []
        
        # 용도별 파생
        purposes = [
            "백팩용", "자전거용", "등산용", "캠핑용", "차량용",
            "사무실용", "여행용", "운동용", "학교용"
        ]
        
        for purpose in purposes:
            if len(derivatives) >= max_count:
                break
            derivatives.append({
                "text": f"{purpose} {base_keyword}",
                "category": "derivative",
                "type": "purpose_derivative",
                "base_keyword": base_keyword,
                "modifier": purpose
            })
        
        return derivatives
    
    def generate_daily_batch(self, total_count: int = 50) -> List[Dict]:
        """일일 배치 키워드 생성 (테스트용 소량)"""
        
        all_keywords = []
        
        # 기본 조합 (70%)
        basic_keywords = self.generate_basic_combinations(int(total_count * 0.7))
        all_keywords.extend(basic_keywords)
        
        # 파생 키워드 (30%)
        for base in self.trending_keywords[:3]:
            derivatives = self.generate_derivative_keywords(base, 5)
            all_keywords.extend(derivatives)
        
        # 중복 제거
        unique_keywords = []
        seen_texts = set()
        
        for keyword in all_keywords:
            if keyword["text"] not in seen_texts:
                seen_texts.add(keyword["text"])
                unique_keywords.append(keyword)
        
        return unique_keywords[:total_count]

# 전역 인스턴스
keyword_generator = KeywordGenerator()

# 테스트 함수
def test_generator():
    """키워드 생성기 테스트"""
    print("🧪 키워드 생성기 테스트 시작...")
    
    # 파생 키워드 테스트
    print("\n📊 '보냉백' 파생 키워드 생성:")
    derivatives = keyword_generator.generate_derivative_keywords("보냉백", 5)
    for i, kw in enumerate(derivatives, 1):
        print(f"  {i}. {kw['text']} ({kw['type']})")
    
    # 기본 조합 테스트  
    print("\n🎯 기본 조합 키워드 생성:")
    basic = keyword_generator.generate_basic_combinations(5)
    for i, kw in enumerate(basic, 1):
        print(f"  {i}. {kw['text']} - {kw['category']}")
    
    # 일일 배치 테스트
    print("\n📦 일일 배치 생성 (처음 10개):")
    daily_batch = keyword_generator.generate_daily_batch(20)
    for i, kw in enumerate(daily_batch[:10], 1):
        print(f"  {i}. {kw['text']} - {kw['category']} ({kw['type']})")
    
    print(f"\n✅ 총 {len(daily_batch)}개 키워드 생성 완료!")

if __name__ == "__main__":
    test_generator()