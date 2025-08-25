import React, { useEffect, useRef, useState } from "react";
import ThinkingDots from "./ThinkingDots";
import TypingEffect from "./TypingEffect";

interface Message {
  sender: "user" | "bot";
  text: string;
}
interface ChatMessagesProps {
  messages: Message[];
  loading: boolean;
}

// 메시지를 포맷팅하는 함수
const formatMessage = (text: string) => {
  // 각 줄을 처리
  const lines = text.split('\n');
  
  return lines.map((line, lineIndex) => {
    // 1. 공지사항 제목 처리
    if (line.match(/^1\. 공지사항 제목:/)) {
      const title = line.replace('1. 공지사항 제목:', '').trim();
      return (
        <div key={lineIndex} className="mb-3">
          <div className="font-semibold mb-1">1. 공지사항 제목</div>
          <div className="ml-4 mb-3">{title}</div>
        </div>
      );
    }
    
    // 2. 주요 내용 요약 처리
    if (line.match(/^2\. 주요 내용 요약:/)) {
      const summary = line.replace('2. 주요 내용 요약:', '').trim();
      return (
        <div key={lineIndex} className="mb-3">
          <div className="font-semibold mb-1">2. 주요 내용 요약</div>
          <div className="ml-4 mb-3">{summary}</div>
        </div>
      );
    }
    
    // 3. 중요 정보 처리 (신청기간, 접수기간 등)
    if (line.match(/^3\. 중요 정보:/)) {
      const info = line.replace('3. 중요 정보:', '').trim();
      return (
        <div key={lineIndex} className="mb-3">
          <div className="font-semibold mb-1">3. 중요 정보</div>
          <div className="ml-4 mb-3">{info}</div>
        </div>
      );
    }
    
    // 4. 신청 방법 처리 (있는 경우에만)
    if (line.match(/^4\. 신청 방법:/)) {
      const method = line.replace('4. 신청 방법:', '').trim();
      return (
        <div key={lineIndex} className="mb-3">
          <div className="font-semibold mb-1">4. 신청 방법</div>
          <div className="ml-4 mb-3">{method}</div>
        </div>
      );
    }
    
    // 5. 공식 링크 처리
    if (line.match(/^5\. 공식 링크$/)) {
      return (
        <div key={lineIndex} className="mb-3">
          <div className="font-semibold mb-1">5. 공식 링크</div>
        </div>
      );
    }
    
    // 공식 링크 다음 줄의 URL 처리
    if (line.match(/^https?:\/\/[^\s]+$/) && lineIndex > 0) {
      const prevLine = lines[lineIndex - 1];
      if (prevLine && prevLine.trim() === '5. 공식 링크') {
        return (
          <div key={lineIndex} className="mb-3">
            <div className="ml-4 mb-3">
              <a
                href={line.trim()}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 underline break-all"
              >
                {line.trim()}
              </a>
            </div>
          </div>
        );
      }
    }
    
    // 일반 텍스트 처리
    if (line.trim() === '') {
      return <br key={lineIndex} />;
    }
    
    // 링크가 포함된 텍스트 처리 (마크다운 형식)
    const urlPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
    if (urlPattern.test(line)) {
      const parts = line.split(urlPattern);
      return (
        <div key={lineIndex} className="mb-2">
          {parts.map((part, partIndex) => {
            if (partIndex % 3 === 0) {
              return <span key={partIndex}>{part}</span>;
            } else if (partIndex % 3 === 1) {
              const linkText = part;
              const linkUrl = parts[partIndex + 1];
              return (
                <a
                  key={partIndex}
                  href={linkUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  {linkText}
                </a>
              );
            }
            return null;
          })}
        </div>
      );
    }
    
    // 일반 텍스트에서 URL 자동 감지
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    if (urlRegex.test(line)) {
      const parts = line.split(urlRegex);
      return (
        <div key={lineIndex} className="mb-2 leading-relaxed">
          {parts.map((part, partIndex) => {
            if (urlRegex.test(part)) {
              return (
                <a
                  key={partIndex}
                  href={part}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline break-all"
                >
                  {part}
                </a>
              );
            }
            return <span key={partIndex}>{part}</span>;
          })}
        </div>
      );
    }
    
    return <div key={lineIndex} className="mb-2 leading-relaxed">{line}</div>;
  });
};

export default function ChatMessages({ messages, loading }: ChatMessagesProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const [typingMessages, setTypingMessages] = useState<Set<number>>(new Set());
  const [completedMessages, setCompletedMessages] = useState<Set<number>>(new Set());
  const lastScrollTime = useRef<number>(0);

  // 스크롤을 맨 아래로 이동하는 함수
  const scrollToBottom = (smooth: boolean = true) => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: smooth ? "smooth" : "auto" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // 타이핑 중에도 스크롤 업데이트를 위한 함수 (성능 최적화)
  const handleTypingUpdate = () => {
    const now = Date.now();
    // 100ms마다만 스크롤 업데이트 (성능 최적화)
    if (now - lastScrollTime.current > 100) {
      scrollToBottom(true);
      lastScrollTime.current = now;
    }
  };

  // 새로운 봇 메시지에 타이핑 효과 적용
  useEffect(() => {
    const botMessages = messages
      .map((msg, idx) => ({ msg, idx }))
      .filter(({ msg }) => msg.sender === "bot");
    
    const lastBotMessage = botMessages[botMessages.length - 1];
    if (lastBotMessage && 
        !typingMessages.has(lastBotMessage.idx) && 
        !completedMessages.has(lastBotMessage.idx)) {
      setTypingMessages(prev => new Set([...prev, lastBotMessage.idx]));
    }
  }, [messages, typingMessages, completedMessages]);

  // 메시지가 변경되면 완료된 메시지 목록 초기화
  useEffect(() => {
    if (messages.length === 0) {
      setCompletedMessages(new Set());
      setTypingMessages(new Set());
    }
  }, [messages.length]);

  const handleTypingComplete = (messageIndex: number) => {
    setTypingMessages(prev => {
      const newSet = new Set(prev);
      newSet.delete(messageIndex);
      return newSet;
    });
    setCompletedMessages(prev => new Set([...prev, messageIndex]));
  };

  return (
    <div className="space-y-6">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`flex items-end gap-3 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
        >
          {msg.sender === "bot" && (
            <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-lg shadow">G</div>
          )}
          <div
            className={`rounded-2xl px-5 py-3 max-w-xl shadow-md text-base font-medium ${
              msg.sender === "user"
                ? "bg-blue-500 text-white rounded-br-3xl"
                : "bg-white text-[#1B3A6B] rounded-bl-3xl border border-blue-100"
            }`}
          >
            {msg.sender === "bot" && typingMessages.has(idx) ? (
              <TypingEffect 
                text={msg.text} 
                speed={10}
                onComplete={() => handleTypingComplete(idx)}
                onTextUpdate={handleTypingUpdate}
                className="leading-relaxed"
                formatFunction={formatMessage}
              />
            ) : (
              formatMessage(msg.text)
            )}
          </div>
          {msg.sender === "user" && (
            <div className="w-9 h-9 rounded-full bg-blue-200 flex items-center justify-center text-blue-700 font-bold text-lg shadow">나</div>
          )}
        </div>
      ))}
      {loading && (
        <div className="flex items-end gap-3 mt-2 justify-start">
          <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-lg shadow">G</div>
          <div className="rounded-2xl px-5 py-3 max-w-xl bg-white text-[#1B3A6B] flex items-center shadow-md border border-blue-100"><ThinkingDots /></div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
} 