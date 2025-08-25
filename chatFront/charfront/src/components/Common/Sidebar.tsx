import React from "react";

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onNewChat?: () => void;
}

const Sidebar = ({ isOpen, onToggle, onNewChat }: SidebarProps) => {
  const sidebarWidth = isOpen ? "w-64" : "w-14";

  const handleNewChat = () => {
    if (onNewChat) onNewChat();
  };
  const handleGoToNotice = () => {
    // 한성대학교 공지사항 페이지로 이동
    window.open('https://www.hansung.ac.kr/hansung/8385/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGaGFuc3VuZyUyRjE0MyUyRmFydGNsTGlzdC5kbyUzRmJic0NsU2VxJTNEJTI2YmJzT3BlbldyZFNlcSUzRCUyNmlzVmlld01pbmUlM0RmYWxzZSUyNnNyY2hDb2x1bW4lM0RzaiUyNnNyY2hXcmQlM0QlMjY%3D', '_blank');
  };
  const handleGoToHomepage = () => {
    // 한성대학교 공식 홈페이지로 이동
    window.open('https://www.hansung.ac.kr', '_blank');
  };

  return (
    <aside
      className={`${sidebarWidth} bg-[#282A2C] text-gray-300 px-3 py-4 flex flex-col justify-between h-screen transition-all duration-300`}
    >
      {/* 상단 영역 */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <button
            className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-[#35373a] hover:shadow-md text-xl hover:scale-110 transition-transform duration-200 leading-none"
            onClick={onToggle}
          >
            <span className="block w-full text-center leading-none">☰</span>
          </button>
        </div>
        {isOpen && (
          <div className="space-y-6">
            {/* Actions */}
            <div className="flex flex-col gap-3">
              <button
                className="flex items-center justify-start gap-2 px-3 py-2 rounded-md bg-[#282A2C] hover:bg-[#4A4B4C] transition border border-transparent "
                onClick={handleNewChat}
              >
                <span className="text-sm font-medium">새 채팅</span>
              </button>
              <button
                className="flex items-center justify-start gap-2 px-3 py-2 rounded-md bg-[#282A2C] hover:bg-[#4A4B4C] transition border border-transparent"
                onClick={handleGoToNotice}
              >
                <span className="text-sm font-medium">공지사항</span>
              </button>
            </div>
          </div>
        )}
      </div>
      {/* 하단 한성대학교 홈페이지 링크 */}
      {isOpen && (
        <div className="mt-8 flex flex-col items-center gap-2">
          <span className="text-xs text-gray-400 mb-1">한성대학교</span>
          <button
            className="px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold shadow-md transition-colors duration-200"
            onClick={handleGoToHomepage}
          >
            공식 홈페이지
          </button>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
