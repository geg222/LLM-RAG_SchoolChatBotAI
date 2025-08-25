import React from "react";

interface ChatHeaderProps {
  isInitial?: boolean;
}

export default function ChatHeader({ isInitial }: ChatHeaderProps) {
  if (isInitial) {
    return (
      <div className="flex flex-col items-center justify-center h-full w-full">
        <span className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 text-transparent bg-clip-text drop-shadow-[0_2px_8px_rgba(124,58,237,0.25)] animate-gradient-x">
          준영님, 안녕하세요
        </span>
        <style>{`
          @keyframes gradient-x {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
          }
          .animate-gradient-x {
            background-size: 200% 200%;
            animation: gradient-x 3s ease-in-out infinite;
          }
        `}</style>
      </div>
    );
  }
  return (
    <div className="text-4xl font-bold text-white mb-8">
      <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600">
        안녕하세요, 준영님.
      </span>
      <br />
      <span>무엇을 도와드릴까요?</span>
    </div>
  );
} 