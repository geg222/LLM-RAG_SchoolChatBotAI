import React, { useState, cloneElement } from "react";
import type { ReactElement } from "react";
import Sidebar from "../components/Common/Sidebar";
import type { ChatPageProps } from "../pages/ChatPage";

interface MainLayoutProps {
  children: ReactElement<ChatPageProps>;
  onNewChat?: () => void;
}

const MainLayout = ({ children, onNewChat }: MainLayoutProps) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const childrenWithProps = cloneElement(children, { onNewChat });

  return (
    <div className="h-screen">
      <div className={`fixed left-0 top-0 h-screen ${isSidebarOpen ? "w-64" : "w-14"} z-20 transition-all duration-300`}>
        <Sidebar isOpen={isSidebarOpen} onToggle={() => setIsSidebarOpen((prev) => !prev)} onNewChat={onNewChat} />
      </div>
      <main className={`${isSidebarOpen ? "ml-64" : "ml-14"} h-screen flex flex-col transition-all duration-300`}>
        {childrenWithProps}
      </main>
    </div>
  );
};

export default MainLayout;
