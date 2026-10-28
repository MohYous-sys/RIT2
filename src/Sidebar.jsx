import { Box, FileText, LayoutGrid, LogIn, LogOut, Plus, Shuffle, X } from "lucide-react";

const navigation = [
  { id: "overview", label: "Overview", icon: LayoutGrid },
  { id: "requests", label: "Requests", icon: FileText, count: 0},
  { id: "inventory", label: "Inventory", icon: Box },
];

export default function Sidebar({ activePage, onNavigate, mobileOpen, onClose, authenticated, onLogin, onLogout }) {
  return (
    <>
      {mobileOpen && (
        <button
          aria-label="Close navigation"
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/55 md:hidden"
        />
      )}
      <aside
        aria-label="Main navigation"
        className={`fixed inset-y-0 left-0 z-50 flex w-[239px] flex-col bg-[#181e2c] px-[23px] pb-[24px] pt-[38px] text-white transition-transform duration-200 md:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex items-center gap-[11px] pl-[8px]">
          <div className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[10px] bg-[#2e61ec]">
            <Plus size={20} strokeWidth={5} aria-hidden="true" />
          </div>
          <span className="text-[17px] font-bold tracking-[-0.5px]">ReliefOps</span>
          <button type="button" onClick={onClose} aria-label="Close menu" className="ml-auto rounded p-1 text-slate-300 hover:bg-white/10 md:hidden">
            <X size={19} />
          </button>
        </div>

        <nav className="mt-[42px] flex flex-col gap-[5px]" aria-label="Primary">
          {navigation.map(({ id, label, icon: Icon, count }) => {
            const selected = activePage === id;
            return (
              <button
                type="button"
                key={id}
                onClick={() => { onNavigate(id); onClose(); }}
                aria-current={selected ? 'page' : undefined}
                className={`flex h-[44px] w-full items-center gap-[12px] rounded-[8px] px-[12px] text-left text-[13px] outline-offset-2 transition-colors focus-visible:outline-2 focus-visible:outline-blue-400 ${selected ? 'bg-[#293449] font-semibold text-white' : 'font-medium text-[#9aa9c1] hover:bg-[#253044] hover:text-white'}`}
              >
                <Icon size={18} strokeWidth={1.8} aria-hidden="true" className={selected ? 'text-white' : 'text-[#91a1ba]'} />
                <span>{label}</span>
                {count != null && <span aria-label={`${count} alerts`} className="ml-auto flex h-[18px] min-w-[19px] items-center justify-center rounded-full bg-[#2e61ec] px-1 text-[10px] font-semibold text-white">{count}</span>}
              </button>
            );
          })}
        </nav>

        <div className="mt-auto border-t border-[#2d3749] pt-[18px]">
          <button
            type="button"
            onClick={authenticated ? onLogout : onLogin}
            className="flex h-[42px] w-full items-center gap-3 rounded-[8px] px-3 text-[13px] font-semibold text-[#c6d0df] transition-colors hover:bg-[#253044] hover:text-white focus-visible:outline-2 focus-visible:outline-blue-400"
          >
            {authenticated ? <LogOut size={18} strokeWidth={1.8} aria-hidden="true" /> : <LogIn size={18} strokeWidth={1.8} aria-hidden="true" />}
            <span>{authenticated ? "Log out" : "Log in"}</span>
          </button>
        </div>
      </aside>
    </>
  );
}
