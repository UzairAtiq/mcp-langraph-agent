import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchPosts } from "@/api";
import { PostItem } from "@/components/PostItem";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowRight, Inbox } from "lucide-react";

export const PostsCard: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ["posts"],
    queryFn: fetchPosts,
    refetchInterval: 15000,
  });

  const posts = data?.posts ?? [];
  const recentPosts = posts.slice(0, 5);

  return (
    <div className="bg-white dark:bg-darkcard dark:border dark:border-neutral-800/80 rounded-3xl p-6 shadow-soft space-y-6 transition-colors text-neutral-900 dark:text-white">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-bold text-lg tracking-tight text-neutral-900 dark:text-white leading-tight">
            Recent Posts
          </h2>
          <p className="text-xs text-mutedText dark:text-neutral-400 font-normal mt-0.5">
            The latest generated content and current approval states
          </p>
        </div>

        <Link
          to="/posts"
          className="inline-flex items-center space-x-1.5 rounded-full px-4 py-2 text-xs font-semibold text-neutral-700 dark:text-neutral-200 bg-neutral-100 dark:bg-neutral-900 hover:bg-neutral-200 dark:hover:bg-neutral-800 border border-transparent dark:border-neutral-800 transition-colors"
        >
          <span>View all</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-28 w-full bg-neutral-100 dark:bg-neutral-900" />
          <Skeleton className="h-28 w-full bg-neutral-100 dark:bg-neutral-900" />
          <Skeleton className="h-28 w-full bg-neutral-100 dark:bg-neutral-900" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && recentPosts.length === 0 && (
        <div className="rounded-2xl border border-dashed border-neutral-200 dark:border-neutral-800 p-8 text-center space-y-2 bg-neutral-50 dark:bg-neutral-900/60">
          <div className="w-10 h-10 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-400 mx-auto flex items-center justify-center">
            <Inbox className="w-5 h-5" />
          </div>
          <p className="text-sm font-semibold text-neutral-800 dark:text-neutral-200">No posts generated yet</p>
          <p className="text-xs text-mutedText dark:text-neutral-400 max-w-sm mx-auto">
            Use the Send to AI form above to generate your first post and push it to Slack for human review.
          </p>
        </div>
      )}

      {/* Posts List */}
      {!isLoading && recentPosts.length > 0 && (
        <div className="space-y-4">
          {recentPosts.map((post, idx) => (
            <PostItem key={post.id || post.post_id || idx} post={post} />
          ))}
        </div>
      )}
    </div>
  );
};
