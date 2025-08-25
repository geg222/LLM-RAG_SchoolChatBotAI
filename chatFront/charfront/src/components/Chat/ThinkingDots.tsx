import React, { useEffect, useState } from "react";

export default function ThinkingDots() {
  const [dots, setDots] = useState("");
  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length < 3 ? prev + "." : ""));
    }, 500);
    return () => clearInterval(interval);
  }, []);
  return <span className="text-lg animate-pulse">생각 중{dots}</span>;
} 