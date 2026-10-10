import React from "react";
import { useTheme } from "@/context/ThemeContext";
import { Sun, Moon } from "lucide-react";

export const ThemeToggle: React.FC<{ className?: string }> = ({ className = "" }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`inline-flex items-center space-x-2 rounded-full px-3.5 py-2 text-xs font-semibold shadow-sm transition-all border ${
        theme === "dark"
          ? "bg-neutral-800 text-neutral-100 border-neutral-700 hover:bg-neutral-700 hover:border-neutral-600"
          : "bg-white text-neutral-800 border-neutral-200 hover:bg-neutral-100"
      } ${className}`}
      aria-label="Toggle color theme"
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
    >
      {theme === "dark" ? (
        <>
          <Sun className="w-3.5 h-3.5 text-accent" />
          <span>Light Mode</span>
        </>
      ) : (
        <>
          <Moon className="w-3.5 h-3.5 text-neutral-700" />
          <span>Dark Mode</span>
        </>
      )}
    </button>
  );
};
