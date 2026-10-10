import React, { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ConnectionCard } from "@/components/ConnectionCard";
import { GenerateCard } from "@/components/GenerateCard";
import { PostsCard } from "@/components/PostsCard";

export const Dashboard: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      gsap.from(".dashboard-card", {
        opacity: 0,
        y: 16,
        duration: 0.45,
        stagger: 0.08,
        ease: "power2.out",
      });
    },
    { scope: containerRef }
  );

  return (
    <div ref={containerRef} className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100 leading-tight">
          Post Dashboard
        </h1>
        <p className="text-xs text-mutedText dark:text-neutral-400 mt-1 font-normal">
          Generate, review and publish to LinkedIn.
        </p>
      </div>

      {/* 2-column Grid on Desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
        <div className="dashboard-card h-[390px] flex flex-col">
          <ConnectionCard />
        </div>
        <div className="dashboard-card h-[390px] flex flex-col">
          <GenerateCard />
        </div>
        <div className="dashboard-card lg:col-span-2">
          <PostsCard />
        </div>
      </div>
    </div>
  );
};
