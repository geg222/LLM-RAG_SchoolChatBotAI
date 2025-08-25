import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Optional
import subprocess
import sys
import os
from core.logger import logger

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class AutoUpdateService:
    """자동 업데이트 서비스"""
    
    def __init__(self, update_interval_hours: int = None):
        # 환경 변수에서 업데이트 간격 가져오기
        if update_interval_hours is None:
            update_interval_hours = int(os.getenv('AUTO_UPDATE_INTERVAL_HOURS', '6'))
        
        self.update_interval_hours = update_interval_hours
        self.last_update_time: Optional[datetime] = None
        self.is_running = False
        self.update_thread: Optional[threading.Thread] = None
        
    def start(self):
        """자동 업데이트 서비스를 시작합니다."""
        if self.is_running:
            logger.warning("자동 업데이트 서비스가 이미 실행 중입니다.")
            return
            
        self.is_running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        logger.info(f"자동 업데이트 서비스가 시작되었습니다. (간격: {self.update_interval_hours}시간)")
        
    def stop(self):
        """자동 업데이트 서비스를 중지합니다."""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("자동 업데이트 서비스가 중지되었습니다.")
        
    def _update_loop(self):
        """업데이트 루프를 실행합니다."""
        while self.is_running:
            try:
                # 첫 실행 시 6시간 대기 후 업데이트
                if self.last_update_time is None:
                    initial_wait_hours = 6
                    initial_wait_seconds = initial_wait_hours * 3600
                    logger.info(f"서버 시작 후 {initial_wait_hours}시간 대기 후 첫 업데이트를 실행합니다...")
                    logger.info(f"첫 업데이트까지 {initial_wait_seconds/3600:.1f}시간 대기 중...")
                    
                    # 6시간 대기
                    time.sleep(initial_wait_seconds)
                    
                    if self.is_running:  # 서비스가 여전히 실행 중인지 확인
                        logger.info("첫 업데이트를 실행합니다...")
                        self._run_update_pipeline()
                        self.last_update_time = datetime.now()
                
                # 이후 정기 업데이트 (6시간 간격)
                next_update = self.last_update_time + timedelta(hours=self.update_interval_hours)
                wait_seconds = (next_update - datetime.now()).total_seconds()
                
                if wait_seconds > 0:
                    logger.info(f"다음 업데이트까지 {wait_seconds/3600:.1f}시간 대기 중...")
                    time.sleep(min(wait_seconds, 300))  # 최대 5분씩 체크
                else:
                    # 업데이트 실행
                    logger.info("정기 업데이트를 실행합니다...")
                    self._run_update_pipeline()
                    self.last_update_time = datetime.now()
                    
            except Exception as e:
                logger.error(f"자동 업데이트 중 오류 발생: {e}")
                time.sleep(300)  # 오류 시 5분 대기
                
    def _run_update_pipeline(self):
        """증분 업데이트 파이프라인을 실행합니다."""
        try:
            # 증분 업데이트 파이프라인 실행 (새로운 공지사항만 처리)
            result = subprocess.run([
                sys.executable, "incremental_update.py"
            ], capture_output=True, text=True, timeout=1800)  # 30분 타임아웃
            
            if result.returncode == 0:
                logger.info("증분 업데이트 파이프라인이 성공적으로 완료되었습니다.")
                if result.stdout:
                    logger.info(f"업데이트 결과: {result.stdout[-500:]}")  # 마지막 500자만
            else:
                logger.error(f"증분 업데이트 파이프라인 실패: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("증분 업데이트 파이프라인이 시간 초과되었습니다.")
        except Exception as e:
            logger.error(f"증분 업데이트 파이프라인 실행 중 오류: {e}")
            
    def force_update(self):
        """강제로 업데이트를 실행합니다."""
        logger.info("강제 업데이트를 실행합니다...")
        self._run_update_pipeline()
        self.last_update_time = datetime.now()
        
    def get_status(self) -> dict:
        """서비스 상태를 반환합니다."""
        return {
            "is_running": self.is_running,
            "last_update_time": self.last_update_time.isoformat() if self.last_update_time else None,
            "next_update_time": (self.last_update_time + timedelta(hours=self.update_interval_hours)).isoformat() if self.last_update_time else None,
            "update_interval_hours": self.update_interval_hours
        }

# 전역 인스턴스
_auto_update_service = None

def get_auto_update_service() -> AutoUpdateService:
    """자동 업데이트 서비스 인스턴스를 반환합니다."""
    global _auto_update_service
    if _auto_update_service is None:
        _auto_update_service = AutoUpdateService()
    return _auto_update_service

def start_auto_update():
    """자동 업데이트 서비스를 시작합니다."""
    service = get_auto_update_service()
    service.start()

def stop_auto_update():
    """자동 업데이트 서비스를 중지합니다."""
    service = get_auto_update_service()
    service.stop() 