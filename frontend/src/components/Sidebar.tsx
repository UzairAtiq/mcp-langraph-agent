import React from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, FileText, Sparkles } from "lucide-react";

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-sidebar text-white rounded-3xl p-6 flex flex-col justify-between shrink-0 shadow-soft">
      <div>
        {/* Logo and Brand */}
        <div className="flex items-center space-x-3 mb-10 px-2">
          <div className="w-10 h-10 rounded-full bg-purpleAccent flex items-center justify-center text-white shadow-sm">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-base tracking-tight text-white leading-tight">
              Post Studio
            </span>
            <span className="text-[11px] text-mutedText font-normal">
              LinkedIn Agent
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="space-y-2">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center space-x-3 px-5 py-3 rounded-full text-sm font-medium transition-all ${
                isActive
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-900"
              }`
            }
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Dashboard</span>
          </NavLink>

          <NavLink
            to="/posts"
            className={({ isActive }) =>
              `flex items-center space-x-3 px-5 py-3 rounded-full text-sm font-medium transition-all ${
                isActive
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-900"
              }`
            }
          >
            <FileText className="w-4 h-4" />
            <span>Posts</span>
          </NavLink>
        </nav>
      </div>

      {/* Footer Branding */}
      <div className="px-3 py-2 text-[11px] text-neutral-500">
        v2.0 · Automated Agent
      </div>
    </aside>
  );
};
