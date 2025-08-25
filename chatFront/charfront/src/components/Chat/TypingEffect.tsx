import React, { useState, useEffect, useRef } from 'react';

interface TypingEffectProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
  className?: string;
  formatFunction?: (text: string) => React.ReactNode;
  onTextUpdate?: () => void; // 텍스트 업데이트 시 호출할 콜백
}

const TypingEffect: React.FC<TypingEffectProps> = ({ 
  text, 
  speed = 10, 
  onComplete, 
  className = "",
  formatFunction,
  onTextUpdate
}) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
        // 텍스트가 업데이트될 때마다 스크롤 업데이트 콜백 호출
        if (onTextUpdate) {
          onTextUpdate();
        }
      }, speed);

      return () => clearTimeout(timer);
    } else if (onComplete) {
      onComplete();
    }
  }, [currentIndex, text, speed, onComplete, onTextUpdate]);

  // 텍스트가 변경되면 타이핑 효과를 다시 시작
  useEffect(() => {
    setDisplayedText('');
    setCurrentIndex(0);
  }, [text]);

  return (
    <div className={className}>
      {formatFunction ? formatFunction(displayedText) : displayedText}
      {currentIndex < text.length && (
        <span className="animate-pulse">|</span>
      )}
    </div>
  );
};

export default TypingEffect; 