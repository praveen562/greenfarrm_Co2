import { NavLink, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/farms", label: "Farms" },
  { to: "/predict", label: "Predict" },
  { to: "/history", label: "History" },
  { to: "/model", label: "Model" },
];

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="flex min-h-screen">
        <aside className="hidden w-60 shrink-0 flex-col border-r border-canopy-100 bg-white px-5 py-6 md:flex">
          <div className="mb-8 flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-canopy-700 font-display text-sm font-semibold text-white">
              GF
            </span>
            <div>
              <p className="font-display text-sm font-semibold leading-tight text-ink">GreenFarm</p>
              <p className="text-[11px] leading-tight text-canopy-600">Carbon AI</p>
            </div>
          </div>

          <nav className="flex flex-1 flex-col gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-canopy-100 text-canopy-800"
                      : "text-ink/70 hover:bg-canopy-50 hover:text-canopy-800"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="mt-auto border-t border-canopy-100 pt-4">
            <p className="truncate text-xs text-ink/60">{user?.full_name}</p>
            <p className="truncate text-[11px] text-ink/40">{user?.email}</p>
            <button
              onClick={handleLogout}
              className="mt-3 w-full rounded-lg border border-canopy-200 px-3 py-1.5 text-xs font-medium text-canopy-800 transition-colors hover:bg-canopy-50"
            >
              Log out
            </button>
          </div>
        </aside>

        <div className="flex flex-1 flex-col">
          <header className="flex items-center justify-between border-b border-canopy-100 bg-white px-5 py-3 md:hidden">
            <p className="font-display text-sm font-semibold">GreenFarm Carbon AI</p>
            <button onClick={handleLogout} className="text-xs text-canopy-700 underline">
              Log out
            </button>
          </header>
          <nav className="flex gap-1 overflow-x-auto border-b border-canopy-100 bg-white px-3 py-2 md:hidden">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium ${
                    isActive ? "bg-canopy-100 text-canopy-800" : "text-ink/60"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <main className="flex-1 px-5 py-6 md:px-10 md:py-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
