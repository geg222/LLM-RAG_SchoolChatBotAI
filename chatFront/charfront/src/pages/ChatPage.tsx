import type { Message } from "../hooks/useChat";
import ChatHeader from "../components/Chat/ChatHeader";
import ChatMessages from "../components/Chat/ChatMessages";
import ChatInput from "../components/Chat/ChatInput";
import React from "react";

export interface ChatPageProps {
  messages: Message[];
  loading: boolean;
  isInitial: boolean;
  showInitial: boolean;
  setShowInitial: React.Dispatch<React.SetStateAction<boolean>>;
  handleSend: (text: string) => Promise<void>;
  resetChat: () => void;
  onNewChat?: () => void;
}

const ChatPage: React.FC<ChatPageProps> = ({
  messages,
  loading,
  isInitial,
  showInitial,
  setShowInitial,
  handleSend,
  resetChat,
  onNewChat,
}) => {
  // onNewChat prop이 있으면 resetChat 대신 그걸 사용, 없으면 내부 resetChat 사용
  const handleNewChat = onNewChat || resetChat;

  return (
    <div className="flex h-screen bg-[#1B1C1D]">
      {/* <Sidebar /> */}
      <div className="flex-1 flex flex-col bg-[#1B1C1D] min-w-0 ml-64">
        <main className="flex-1 overflow-y-auto p-6 bg-[#1B1C1D] relative">
          {/* 중앙 인사말 페이드 */}
          <div
            className={`absolute inset-0 flex items-center justify-center transition-opacity duration-500 ${
              showInitial && isInitial ? "opacity-100 z-10" : "opacity-0 pointer-events-none"
            }`}
          >
            <ChatHeader isInitial />
          </div>
          {/* 채팅 영역 페이드 */}
          <div
            className={`max-w-3xl mx-auto w-full transition-opacity duration-500 ${
              !showInitial || !isInitial ? "opacity-100" : "opacity-0 pointer-events-none"
            }`}
          >
            {!isInitial && <ChatHeader />}
            {!isInitial && <ChatMessages messages={messages} loading={loading} />}
          </div>
        </main>
        <div className="w-full flex justify-center items-center">
          <div className="w-full max-w-3xl">
            <ChatInput onSend={handleSend} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
