import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./App.css";
import ChatPage from './pages/ChatPage';
import MainLayout from './layout/MainLayout';
import { useChat } from './hooks/useChat';

// ChatPage를 위한 래퍼 컴포넌트
const ChatPageWrapper = () => {
  const chat = useChat();
  return (
    <MainLayout onNewChat={chat.resetChat}>
      <ChatPage {...chat} />
    </MainLayout>
  );
};

const router = createBrowserRouter([
  {
    path: "/",
    element: <ChatPageWrapper />,
  },
]);

function App() {
  return (
    <>
      <RouterProvider router={router} />
    </>
  );
}

export default App;
