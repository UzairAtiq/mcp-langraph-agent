import React from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { type Post } from "@/api";
import { Calendar, Hash } from "lucide-react";

interface PostItemProps {
  post: Post;
}

export const PostItem: React.FC<PostItemProps> = ({ post }) => {
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

  return (
    <div className="bg-white rounded-3xl p-6 shadow-soft border border-neutral-100 flex flex-col justify-between space-y-4 transition-all hover:shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-mono text-neutral-500">
          <Hash className="w-3.5 h-3.5 text-neutral-400" />
          <span>{postId}</span>
        </div>
        <StatusBadge status={post.status} />
      </div>

      <div className="text-sm text-neutral-900 font-normal leading-relaxed whitespace-pre-wrap break-words">
        {post.content}
      </div>

      <div className="flex items-center space-x-2 pt-2 border-t border-neutral-100 text-[11px] text-mutedText">
        <Calendar className="w-3 h-3 text-neutral-400" />
        <span>{formattedDate}</span>
      </div>
    </div>
  );
};
