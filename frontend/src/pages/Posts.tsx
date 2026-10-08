import React, { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { useQuery } from "@tanstack/react-query";
import { fetchPosts } from "@/api";
import { PostItem } from "@/components/PostItem";
import { Skeleton } from "@/components/ui/skeleton";
import { Inbox } from "lucide-react";

export const Posts: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["posts"],
    queryFn: fetchPosts,
    refetchInterval: 15000,
  });

  const posts = data?.posts ?? [];

  useGSAP(
    () => {
      if (!isLoading && posts.length > 0) {
        gsap.from(".post-card-item", {
          opacity: 0,
          y: 14,
          duration: 0.4,
          stagger: 0.08,
          ease: "power2.out",
        });
      }
    },
    { scope: containerRef, dependencies: [isLoading, posts.length] }
  );

  return (
    <div ref={containerRef} className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900 leading-tight">
          All Posts
        </h1>
        <p className="text-xs text-mutedText mt-1 font-normal">
          Chronological record of generated LinkedIn posts and approvals.
        </p>
      </div>

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full bg-white/80" />
          <Skeleton className="h-32 w-full bg-white/80" />
          <Skeleton className="h-32 w-full bg-white/80" />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && posts.length === 0 && (
        <div className="bg-white rounded-3xl p-12 text-center space-y-3 shadow-soft border border-neutral-100">
          <div className="w-12 h-12 rounded-full bg-neutral-100 text-neutral-400 mx-auto flex items-center justify-center">
            <Inbox className="w-6 h-6" />
          </div>
          <p className="text-base font-semibold text-neutral-800">No posts stored yet</p>
          <p className="text-xs text-mutedText max-w-sm mx-auto">
            Head over to the Dashboard to generate your first AI post and start tracking.
          </p>
        </div>
      )}

      {/* Posts List */}
      {!isLoading && posts.length > 0 && (
        <div className="space-y-4">
          {posts.map((post, idx) => (
            <div key={post.id || post.post_id || idx} className="post-card-item">
              <PostItem post={post} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
