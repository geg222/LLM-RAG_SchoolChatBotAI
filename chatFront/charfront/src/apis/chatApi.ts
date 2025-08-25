export async function fetchChatResponse(message: string, sessionId?: string, language = "한국어") {
  try {
  const res = await fetch("http://localhost:8000/api/chat/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      message, 
      language,
      session_id: sessionId || 'default_session'
    }),
  });

    if (!res.ok) {
      // HTTP 상태 코드 오류 처리
      if (res.status === 404) {
        throw new Error("서버를 찾을 수 없습니다. 서버가 실행 중인지 확인해주세요.");
      } else if (res.status === 500) {
        throw new Error("서버 내부 오류가 발생했습니다.");
      } else if (res.status === 503) {
        throw new Error("서버가 일시적으로 사용할 수 없습니다.");
      } else {
        throw new Error(`서버 오류 (${res.status}): ${res.statusText}`);
      }
    }

  const data = await res.json();
    
    if (data.answer) {
      return data.answer;
    } else if (data.error) {
      throw new Error(data.error);
    } else {
      throw new Error("서버에서 예상치 못한 응답을 받았습니다.");
    }
    
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.");
    }
    throw error;
  }
}
