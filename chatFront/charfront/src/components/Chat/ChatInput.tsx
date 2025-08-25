import React, { useState } from "react";
import chatOk from "../../assets/chatOk.svg";

interface ChatInputProps {
  onSend?: (text: string) => void;
}

const ChatInput = ({ onSend }: ChatInputProps) => {
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim()) return;
    onSend?.(value);
    setValue("");
  };

  return (
    <>
      <form
        className="w-full px-4 py-6 bg-[#1B1C1D] sticky bottom-0 z-10"
        onSubmit={handleSubmit}
      >
        <div className="w-full max-w-3xl mx-auto flex items-center gap-3 px-5 py-4 rounded-full border border-[#3a3a3a] bg-[#1c1c1c]">
          <div className="flex-1 relative h-10">
            <textarea
              style={{ textAlign: "left" }}
              className="w-full max-h-60 bg-transparent text-white placeholder-gray-400 focus:outline-none text-base resize-none overflow-hidden pr-2 py-2 break-words"
              placeholder="스쿨캐치에게 물어보기"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = "auto";
                target.style.height = `${target.scrollHeight}px`;
              }}
              onKeyDown={(e) => {
                // IME(한글 등) 조합 중이면 무시
                if ((e as any).nativeEvent.isComposing) return;
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  if (value.trim()) {
                    onSend?.(value);
                    setValue("");
                  }
                }
              }}
            />
          </div>
          <button
            type="submit"
            className="w-10 h-10 rounded-full bg-[#2a2a2a] hover:bg-[#3a3a3a] flex items-center justify-center"
            aria-label="Submit"
          >
            <img src={chatOk} alt="전송" width={20} height={20} />
          </button>
        </div>
      </form>
      <style>{`
        textarea::placeholder {
          text-align: left;
        }
      `}</style>
    </>
  );
};

export default ChatInput;
