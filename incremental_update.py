#!/usr/bin/env python3
"""
한성대학교 챗봇 증분 업데이트 파이프라인
crawl_incremental.py -> ocrmac_incremental.py -> upload_incremental.py 순서로 실행
새로운 공지사항만 처리하여 효율적으로 업데이트
"""

import subprocess
import sys
import time
import os
from datetime import datetime

def run_script(script_name, description):
    """스크립트를 실행하고 결과를 반환합니다."""
    print(f"\n{'='*60}")
    print(f"{description} 시작: {script_name}")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        # 스크립트 실행
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        print(f"{description} 완료!")
        print(f"출력:\n{result.stdout}")
        
        if result.stderr:
            print(f"경고/오류:\n{result.stderr}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"{description} 실패!")
        print(f"오류 코드: {e.returncode}")
        print(f"출력:\n{e.stdout}")
        print(f"오류:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {script_name}")
        return False
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return False

def main():
    """메인 증분 업데이트 파이프라인 실행 함수"""
    print("한성대학교 챗봇 증분 업데이트 파이프라인 시작")
    print(f"실행 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("새로운 공지사항만 처리하여 효율적으로 업데이트합니다.")
    
    # 실행할 스크립트 목록
    scripts = [
        ("crawl_incremental.py", "새로운 학사 공지사항 크롤링"),
        ("ocrmac_incremental.py", "새로운 이미지 OCR 처리"),
        ("upload_incremental.py", "새로운 공지사항 벡터 DB 업로드")
    ]
    
    # 각 스크립트 실행
    success_count = 0
    total_scripts = len(scripts)
    
    for script_name, description in scripts:
        if run_script(script_name, description):
            success_count += 1
            print(f"{description} 성공!")
        else:
            print(f"{description} 실패! 파이프라인 중단")
            break
        
        # 스크립트 간 잠시 대기 (서버 부하 방지)
        if script_name != scripts[-1][0]:  # 마지막 스크립트가 아니면
            print(f"3초 대기 중...")
            time.sleep(3)
    
    # 결과 요약
    print(f"\n{'='*60}")
    print(f"증분 업데이트 파이프라인 실행 결과")
    print(f"{'='*60}")
    print(f"성공: {success_count}/{total_scripts}")
    print(f"실패: {total_scripts - success_count}/{total_scripts}")
    
    if success_count == total_scripts:
        print(f"모든 증분 업데이트가 성공적으로 완료되었습니다!")
        return True
    else:
        print(f"일부 증분 업데이트가 실패했습니다.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")
        sys.exit(1) 