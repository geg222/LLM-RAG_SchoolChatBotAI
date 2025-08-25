import { useState } from "react";
import { fetchChatResponse } from "../apis/chatApi";

export interface Message {
  sender: "user" | "bot";
  text: string;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const isInitial = messages.length === 0;
  const [showInitial, setShowInitial] = useState(true);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  const handleSend = async (text: string) => {
    if (isInitial) setShowInitial(false);
    setMessages((prev) => [...prev, { sender: "user", text }]);
    setLoading(true);
    
    try {
      const botReply = await fetchChatResponse(text, sessionId);
      setMessages((prev) => [...prev, { sender: "bot", text: botReply }]);
    } catch (error) {
      // 구체적인 오류 메시지 표시
      const errorMessage = error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.";
      setMessages((prev) => [...prev, { 
        sender: "bot", 
        text: `😔 ${errorMessage}\n\n잠시 후 다시 시도해보세요.` 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const resetChat = () => {
    setMessages([]);
    setShowInitial(true);
    // 새로운 세션 ID 생성
    window.location.reload(); // 간단한 방법으로 새 세션 시작
  };

  return {
    messages,
    loading,
    isInitial,
    showInitial,
    setShowInitial,
    handleSend,
    resetChat,
    sessionId,
  };
} 