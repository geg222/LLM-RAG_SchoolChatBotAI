from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat_api import router as chat_router
from api.auto_update_api import router as auto_update_router
from service.auto_update_service import start_auto_update, stop_auto_update, get_auto_update_service

app = FastAPI(title="한성대학교 챗봇 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(auto_update_router, prefix="/api/auto-update", tags=["auto-update"])

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    print("한성대학교 챗봇 서버가 시작되었습니다.")
    print("자동 업데이트 서비스를 시작합니다...")
    start_auto_update()

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행되는 이벤트"""
    print("서버를 종료합니다...")
    stop_auto_update()
    print("자동 업데이트 서비스가 중지되었습니다.")