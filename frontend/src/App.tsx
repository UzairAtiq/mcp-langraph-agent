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
        <div className="min-h-screen bg-[#E5E5E5] p-3 md:p-4 flex items-stretch font-sans text-neutral-900">
          <div className="w-full max-w-7xl mx-auto rounded-[32px] p-3 flex flex-col md:flex-row gap-4">
            {/* Dark Sidebar */}
            <Sidebar />

            {/* Main Application Area */}
            <main className="flex-1 min-w-0 py-2 px-1 md:px-4 overflow-y-auto">
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
