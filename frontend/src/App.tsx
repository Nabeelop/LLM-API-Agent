import TopBar from "./components/TopBar";
import Sidebar from "./components/SideBar";
import ChatWindow from "./components/ChatWindow";

export default function App() {
  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <TopBar />
      <div style={{ flex: 1, display: "flex" }}>
        <Sidebar />
        <ChatWindow />
      </div>
    </div>
  );
}
