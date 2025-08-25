from fastapi import APIRouter, HTTPException
from service.auto_update_service import get_auto_update_service
from core.logger import logger

router = APIRouter()

@router.get("/status")
async def get_auto_update_status():
    """자동 업데이트 서비스 상태를 조회합니다."""
    try:
        service = get_auto_update_service()
        status = service.get_status()
        return {
            "message": "자동 업데이트 서비스 상태",
            "status": status
        }
    except Exception as e:
        logger.error(f"자동 업데이트 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="상태 조회 중 오류가 발생했습니다.")

@router.post("/force-update")
async def force_update():
    """강제로 업데이트를 실행합니다."""
    try:
        service = get_auto_update_service()
        service.force_update()
        return {
            "message": "강제 업데이트가 시작되었습니다.",
            "status": "running"
        }
    except Exception as e:
        logger.error(f"강제 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail="강제 업데이트 중 오류가 발생했습니다.")

@router.post("/start")
async def start_auto_update():
    """자동 업데이트 서비스를 시작합니다."""
    try:
        service = get_auto_update_service()
        service.start()
        return {
            "message": "자동 업데이트 서비스가 시작되었습니다.",
            "status": "started"
        }
    except Exception as e:
        logger.error(f"자동 업데이트 시작 실패: {e}")
        raise HTTPException(status_code=500, detail="서비스 시작 중 오류가 발생했습니다.")

@router.post("/stop")
async def stop_auto_update():
    """자동 업데이트 서비스를 중지합니다."""
    try:
        service = get_auto_update_service()
        service.stop()
        return {
            "message": "자동 업데이트 서비스가 중지되었습니다.",
            "status": "stopped"
        }
    except Exception as e:
        logger.error(f"자동 업데이트 중지 실패: {e}")
        raise HTTPException(status_code=500, detail="서비스 중지 중 오류가 발생했습니다.") 