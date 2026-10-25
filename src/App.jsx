import { useState } from "react";
import { ChevronRight } from "lucide-react";
import Sidebar from "./Sidebar";

export default function App() {
  const [activePage, setActivePage] = useState("overview");

  function navigate(page) {
    setActivePage(page);
  }

  return (
    <div className="min-h-screen w-full bg-[#f7f9fc] text-[#111a2e]">
      <Sidebar
        activePage={activePage}
        onNavigate={navigate}
        mobileOpen={false}
        onClose={() => {}}
      />
      <div className="min-h-screen min-w-0 md:ml-[239px]">
        <header className="flex h-[78px] items-center border-b border-[#dbe3ee] bg-white px-5 md:px-[30px]">
          <div className="truncate text-[12px] text-[#8196b5]">
            ReliefOps <ChevronRight size={13} className="mx-1 inline-block" />
            <span className="font-semibold text-[#344568]">{activePage}</span>
          </div>
        </header>
      </div>
    </div>
  );
}