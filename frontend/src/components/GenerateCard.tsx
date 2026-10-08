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
    <div className="bg-white dark:bg-darkcard dark:border dark:border-neutral-800/80 rounded-3xl p-6 shadow-soft flex flex-col justify-between h-full overflow-hidden transition-colors text-neutral-900 dark:text-white">
      <div className="space-y-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <div className="w-7 h-7 rounded-full bg-purpleAccent/10 text-purpleAccent flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <h2 className="font-bold text-lg tracking-tight text-neutral-900 dark:text-white leading-tight">
              Send to AI
            </h2>
          </div>
          <p className="text-xs text-mutedText dark:text-neutral-400 font-normal">
            Generate an engaging LinkedIn post and send it directly to Slack for approval.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label htmlFor="topic-input" className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300 mb-1.5">
              Post Topic
            </label>
            <Input
              id="topic-input"
              type="text"
              placeholder="e.g. AI advancements and modern software engineering"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={generateMutation.isPending}
              className="dark:bg-neutral-900 dark:border-neutral-800 h-9 text-xs"
            />
          </div>

          <Button
            type="submit"
            disabled={generateMutation.isPending}
            className="w-full bg-accent text-neutral-950 hover:bg-accent-hover font-bold shadow-sm h-9 text-xs"
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
                <span>Generating with AI...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 mr-2" />
                <span>Generate Post</span>
              </>
            )}
          </Button>
        </form>
      </div>

      {/* Result / Output section with fixed remaining height */}
      <div className="flex-1 min-h-0 pt-3 flex flex-col">
        {generateMutation.isSuccess && generatedPost ? (
          <div className="flex-1 min-h-0 flex flex-col rounded-2xl bg-neutral-50 dark:bg-neutral-900/80 border border-neutral-200 dark:border-neutral-800/80 p-3.5 space-y-2 overflow-hidden">
            <div className="flex items-center justify-between text-xs shrink-0">
              <div className="flex items-center space-x-1.5 text-neutral-800 dark:text-neutral-200 font-semibold truncate">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                <span className="truncate">Post #{generatedPost.post_id} sent to Slack</span>
              </div>
              <button
                type="button"
                onClick={() => handleCopy(generatedPost.generated_content)}
                className="inline-flex items-center space-x-1 text-[11px] text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors shrink-0 ml-2"
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
            <div className="flex-1 min-h-0 overflow-y-auto text-xs text-neutral-800 dark:text-neutral-200 whitespace-pre-wrap leading-relaxed pr-1 select-text">
              {generatedPost.generated_content}
            </div>
          </div>
        ) : generateMutation.isError ? (
          <div className="flex-1 min-h-0 rounded-2xl bg-danger/10 border border-danger/30 p-3 flex items-start space-x-2 text-xs text-danger overflow-y-auto">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{generateMutation.error?.message || "Failed to generate post. Please check your connection."}</span>
          </div>
        ) : (
          <div className="flex-1 min-h-0 rounded-2xl border border-dashed border-neutral-200 dark:border-neutral-800/80 p-3 flex flex-col items-center justify-center text-center">
            {generateMutation.isPending ? (
              <div className="space-y-1.5 flex flex-col items-center">
                <Loader2 className="w-4 h-4 text-purpleAccent animate-spin" />
                <p className="text-xs text-neutral-600 dark:text-neutral-400">
                  Generating post with AI...
                </p>
              </div>
            ) : (
              <p className="text-xs text-mutedText dark:text-neutral-500">
                Generated post & Slack status will appear here
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
