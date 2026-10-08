import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "@/components/Sidebar";
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
      <BrowserRouter>
        {/* Viewport canvas backdrop */}
        <div className="min-h-screen bg-[#D4D4D8] p-2 md:p-5 flex items-center justify-center font-sans text-neutral-900">
          {/* Main Dark App Container */}
          <div className="w-full max-w-[1550px] h-[calc(100vh-2.5rem)] min-h-[750px] bg-sidebar rounded-[40px] p-3 md:p-4 flex flex-col md:flex-row shadow-2xl overflow-hidden">
            {/* Sidebar taking full left space inside the dark container */}
            <Sidebar />

            {/* Light Content Page overlayed on top of the dark frame */}
            <main className="flex-1 min-w-0 bg-[#E5E5E5] rounded-[32px] p-6 md:p-8 overflow-y-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/posts" element={<Posts />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
