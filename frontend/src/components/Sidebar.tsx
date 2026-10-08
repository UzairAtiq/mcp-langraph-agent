import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, FileText, Sparkles, ChevronLeft, ChevronRight } from "lucide-react";

export const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={`bg-sidebar text-white rounded-3xl flex flex-col justify-between shrink-0 shadow-soft transition-all duration-300 ease-in-out ${
        isCollapsed ? "w-20 p-4 items-center" : "w-64 p-6"
      }`}
    >
      <div className="w-full">
        {/* Header with Logo and Collapse Toggle */}
        <div
          className={`flex items-center mb-10 ${
            isCollapsed ? "flex-col space-y-4 px-0 justify-center" : "justify-between px-2"
          }`}
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-purpleAccent flex items-center justify-center text-white shadow-sm shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col overflow-hidden">
                <span className="font-bold text-base tracking-tight text-white leading-tight truncate">
                  Post Studio
                </span>
                <span className="text-[11px] text-mutedText font-normal truncate">
                  LinkedIn Agent
                </span>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={() => setIsCollapsed((prev) => !prev)}
            className="w-7 h-7 rounded-full bg-neutral-900 hover:bg-neutral-800 text-neutral-400 hover:text-white flex items-center justify-center transition-colors"
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="space-y-2 w-full">
          <NavLink
            to="/"
            end
            title={isCollapsed ? "Dashboard" : undefined}
            className={({ isActive }) =>
              `flex items-center rounded-full text-sm font-medium transition-all ${
                isCollapsed
                  ? "justify-center w-12 h-12 mx-auto"
                  : "space-x-3 px-5 py-3"
              } ${
                isActive
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-900"
              }`
            }
          >
            <LayoutDashboard className="w-4 h-4 shrink-0" />
            {!isCollapsed && <span>Dashboard</span>}
          </NavLink>

          <NavLink
            to="/posts"
            title={isCollapsed ? "Posts" : undefined}
            className={({ isActive }) =>
              `flex items-center rounded-full text-sm font-medium transition-all ${
                isCollapsed
                  ? "justify-center w-12 h-12 mx-auto"
                  : "space-x-3 px-5 py-3"
              } ${
                isActive
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-900"
              }`
            }
          >
            <FileText className="w-4 h-4 shrink-0" />
            {!isCollapsed && <span>Posts</span>}
          </NavLink>
        </nav>
      </div>

      {/* Footer Branding */}
      <div
        className={`text-[11px] text-neutral-500 w-full ${
          isCollapsed ? "text-center py-2" : "px-3 py-2"
        }`}
      >
        {isCollapsed ? "v2.0" : "v2.0 · Automated Agent"}
      </div>
    </aside>
  );
};
