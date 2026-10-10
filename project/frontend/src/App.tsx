import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/context/ThemeContext";
import { Sidebar } from "@/components/Sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Dashboard } from "@/pages/Dashboard";
import { Posts } from "@/pages/Posts";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          {/* Viewport canvas backdrop */}
          <div className="min-h-screen bg-[#D4D4D8] dark:bg-[#080808] p-2 md:p-5 flex items-center justify-center font-sans text-neutral-900 dark:text-neutral-100 transition-colors duration-300">
            {/* Main Dark App Container */}
            <div className="w-full max-w-[1550px] h-[calc(100vh-2.5rem)] min-h-[750px] bg-sidebar rounded-[40px] p-3 md:p-4 flex flex-col md:flex-row shadow-2xl border border-neutral-900 dark:border-neutral-800/80 overflow-hidden">
              {/* Sidebar taking full left space inside dark container */}
              <Sidebar />

              {/* Main Content Area overlayed on top */}
              <main className="flex-1 min-w-0 bg-[#E5E5E5] dark:bg-[#121212] rounded-[32px] p-6 md:p-8 overflow-y-auto flex flex-col justify-between transition-colors duration-300">
                <div className="space-y-6">
                  {/* Top Bar with Theme Toggle on Top */}
                  <div className="flex items-center justify-end pb-2">
                    <ThemeToggle />
                  </div>

                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/posts" element={<Posts />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </div>
              </main>
            </div>
          </div>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
