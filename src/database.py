#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 초기화 및 모델 정의
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

def init_database():
    """데이터베이스 및 테이블 초기화"""
    
    # 데이터 폴더 생성
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 데이터베이스 파일 경로
    db_path = data_dir / "keywords.db"
    
    # 데이터베이스 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 키워드 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text VARCHAR(100) UNIQUE NOT NULL,
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_analyzed TIMESTAMP,
            priority INTEGER DEFAULT 3,
            status VARCHAR(20) DEFAULT 'new',
            base_keyword VARCHAR(100),
            is_derivative BOOLEAN DEFAULT 0
        )
    """)
    
    # 분석 결과 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword_id INTEGER NOT NULL,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            growth_rate DECIMAL(5,2),
            is_seasonal BOOLEAN,
            acceleration DECIMAL(5,2),
            stage VARCHAR(20),
            promise_score INTEGER,
            year1_avg DECIMAL(5,2),
            year2_avg DECIMAL(5,2),
            year3_avg DECIMAL(5,2),
            trend_data TEXT,
            FOREIGN KEY (keyword_id) REFERENCES keywords (id)
        )
    """)
    
    # 사용자 액션 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword_id INTEGER NOT NULL,
            action VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (keyword_id) REFERENCES keywords (id)
        )
    """)
    
    # 일일 통계 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE NOT NULL,
            keywords_analyzed INTEGER DEFAULT 0,
            new_discoveries INTEGER DEFAULT 0,
            high_potential INTEGER DEFAULT 0,
            api_calls INTEGER DEFAULT 0
        )
    """)
    
    # 인덱스 생성
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords_status ON keywords(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_keywords_priority ON keywords(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_keyword_id ON analysis_results(keyword_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_score ON analysis_results(promise_score)")
    
    # 변경사항 저장 및 연결 종료
    conn.commit()
    conn.close()
    
    print(f"✅ 데이터베이스 초기화 완료: {db_path}")

def get_db_connection():
    """데이터베이스 연결 반환"""
    db_path = Path("data") / "keywords.db"
    return sqlite3.connect(db_path)

def insert_keyword(text: str, category: str = None, base_keyword: str = None, 
                  is_derivative: bool = False, priority: int = 3):
    """새 키워드 삽입"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO keywords 
            (text, category, base_keyword, is_derivative, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (text, category, base_keyword, is_derivative, priority))
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"키워드 삽입 오류: {e}")
        return None
    finally:
        conn.close()

def insert_analysis_result(keyword_id: int, analysis_data: dict):
    """분석 결과 삽입"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO analysis_results 
            (keyword_id, growth_rate, is_seasonal, acceleration, stage, 
             promise_score, year1_avg, year2_avg, year3_avg, trend_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            keyword_id,
            analysis_data.get('growth_rate'),
            analysis_data.get('is_seasonal'),
            analysis_data.get('acceleration'),
            analysis_data.get('stage'),
            analysis_data.get('promise_score'),
            analysis_data.get('year1_avg'),
            analysis_data.get('year2_avg'), 
            analysis_data.get('year3_avg'),
            str(analysis_data.get('trend_data', ''))
        ))
        
        # 키워드 테이블의 last_analyzed 업데이트
        cursor.execute("""
            UPDATE keywords 
            SET last_analyzed = CURRENT_TIMESTAMP, status = 'completed'
            WHERE id = ?
        """, (keyword_id,))
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"분석 결과 삽입 오류: {e}")
        return None
    finally:
        conn.close()

def get_today_discoveries():
    """오늘 발견된 키워드들 조회"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT k.text, ar.growth_rate, ar.stage, ar.promise_score,
                   strftime('%H:%M', k.created_at) as discovered_time,
                   k.category
            FROM keywords k
            JOIN analysis_results ar ON k.id = ar.keyword_id
            WHERE date(k.created_at) = date('now')
            AND ar.promise_score >= ?
            ORDER BY ar.promise_score DESC, k.created_at DESC
            LIMIT 20
        """, (70,))  # 70점 이상만
        
        results = cursor.fetchall()
        
        keywords = []
        for row in results:
            keywords.append({
                "keyword": row[0],
                "growth_rate": row[1],
                "stage": row[2],
                "score": row[3],
                "discovered_time": row[4],
                "category": row[5]
            })
        
        return keywords
    except Exception as e:
        print(f"오늘 발견 조회 오류: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    # 테스트 실행
    init_database()
    
    # 테스트 데이터 삽입
    keyword_id = insert_keyword("보냉백", "아웃도어")
    if keyword_id:
        test_analysis = {
            "growth_rate": 150.5,
            "is_seasonal": False,
            "acceleration": 45.2,
            "stage": "growth",
            "promise_score": 85,
            "year1_avg": 15.2,
            "year2_avg": 28.7,
            "year3_avg": 48.1
        }
        insert_analysis_result(keyword_id, test_analysis)
        print("✅ 테스트 데이터 삽입 완료")