import React, { useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { type Post } from "@/api";
import { Calendar, Hash, ChevronDown, ChevronUp } from "lucide-react";

interface PostItemProps {
  post: Post;
}

export const PostItem: React.FC<PostItemProps> = ({ post }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const postId = post.id || post.post_id || "post-item";

  const formattedDate = React.useMemo(() => {
    if (!post.created_at) return "—";
    try {
      return new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(post.created_at));
    } catch {
      return post.created_at;
    }
  }, [post.created_at]);

  const isLong = React.useMemo(() => {
    const text = post.content || "";
    return text.length > 160 || text.split("\n").length > 3;
  }, [post.content]);

  return (
    <div className="bg-white dark:bg-neutral-900/80 rounded-3xl p-6 shadow-soft border border-neutral-100 dark:border-neutral-800/80 flex flex-col justify-between space-y-4 transition-all hover:shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-mono text-neutral-500 dark:text-neutral-400">
          <Hash className="w-3.5 h-3.5 text-neutral-400 dark:text-neutral-500" />
          <span>{postId}</span>
        </div>
        <StatusBadge status={post.status} />
      </div>

      <div className="space-y-2">
        <div
          className={`text-sm text-neutral-900 dark:text-neutral-100 font-normal leading-relaxed whitespace-pre-wrap break-words ${
            !isExpanded && isLong ? "line-clamp-3" : ""
          }`}
        >
          {post.content}
        </div>

        {isLong && (
          <button
            type="button"
            onClick={() => setIsExpanded((prev) => !prev)}
            className="inline-flex items-center space-x-1.5 text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white transition-colors pt-1"
          >
            <span>{isExpanded ? "Show less" : "Show full post"}</span>
            {isExpanded ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>
        )}
      </div>

      <div className="flex items-center space-x-2 pt-2 border-t border-neutral-100 dark:border-neutral-800/80 text-[11px] text-mutedText dark:text-neutral-400">
        <Calendar className="w-3 h-3 text-neutral-400 dark:text-neutral-500" />
        <span>{formattedDate}</span>
      </div>
    </div>
  );
};
