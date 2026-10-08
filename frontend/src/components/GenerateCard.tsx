import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { generatePost, type GeneratePostResponse } from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles, Loader2, CheckCircle2, AlertCircle, Copy, Check } from "lucide-react";

export const GenerateCard: React.FC = () => {
  const [topic, setTopic] = useState("");
  const [copied, setCopied] = useState(false);
  const queryClient = useQueryClient();

  const generateMutation = useMutation({
    mutationFn: (topicText: string) => generatePost(topicText),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const prompt = topic.trim() || "AI advancements and modern software engineering";
    generateMutation.mutate(prompt);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const generatedPost: GeneratePostResponse | undefined = generateMutation.data;

  return (
    <div className="bg-white dark:bg-[#18181B] dark:border dark:border-neutral-800 rounded-3xl p-6 shadow-soft flex flex-col justify-between space-y-5 h-full transition-colors">
      <div>
        <div className="flex items-center space-x-2 mb-1">
          <div className="w-7 h-7 rounded-full bg-purpleAccent/10 text-purpleAccent flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <h2 className="font-bold text-lg tracking-tight text-neutral-900 dark:text-neutral-100 leading-tight">
            Send to AI
          </h2>
        </div>
        <p className="text-xs text-mutedText dark:text-neutral-400 font-normal">
          Generate an engaging LinkedIn post and send it directly to Slack for approval.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="topic-input" className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-2">
            Post Topic
          </label>
          <Input
            id="topic-input"
            type="text"
            placeholder="e.g. AI advancements and modern software engineering"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={generateMutation.isPending}
          />
        </div>

        <Button
          type="submit"
          disabled={generateMutation.isPending}
          className="w-full bg-accent text-neutral-950 hover:bg-accent-hover font-bold shadow-sm"
        >
          {generateMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              <span>Generating with AI...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              <span>Generate Post</span>
            </>
          )}
        </Button>
      </form>

      {/* Success notification & Full Content */}
      {generateMutation.isSuccess && generatedPost && (
        <div className="rounded-2xl bg-neutral-50 dark:bg-neutral-900/90 border border-neutral-200 dark:border-neutral-800 p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center space-x-1.5 text-neutral-800 dark:text-neutral-200 font-semibold">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Post #{generatedPost.post_id} created & sent to Slack</span>
            </div>
            <button
              type="button"
              onClick={() => handleCopy(generatedPost.generated_content)}
              className="inline-flex items-center space-x-1 text-[11px] text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-emerald-500 font-medium">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
          <div className="text-xs text-neutral-800 dark:text-neutral-200 whitespace-pre-wrap leading-relaxed max-h-56 overflow-y-auto pr-1">
            {generatedPost.generated_content}
          </div>
        </div>
      )}

      {/* Error state */}
      {generateMutation.isError && (
        <div className="rounded-2xl bg-danger/10 border border-danger/30 p-3 flex items-start space-x-2 text-xs text-danger">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{generateMutation.error?.message || "Failed to generate post. Please check your connection."}</span>
        </div>
      )}
    </div>
  );
};
