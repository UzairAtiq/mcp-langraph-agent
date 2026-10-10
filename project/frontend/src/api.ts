export const GENERATE_HTTP_METHOD: "POST" | "GET" = "POST";

export interface HealthResponse {
  status: string;
  service: string;
  database: string;
  linkedin_authenticated: boolean;
}

export interface LinkedInStatusResponse {
  authenticated: boolean;
  token_preview?: string;
  redirect_uri?: string;
  person_urn?: string | null;
  expires_at?: string | null;
  refresh_token_available?: boolean;
  scope?: string | null;
  updated_at?: string | null;
  message?: string;
}

export interface Post {
  id?: string;
  post_id?: string;
  content: string;
  status: string;
  created_at: string;
  profile_id?: string;
}

export interface PostsResponse {
  total_count: number;
  posts: Post[];
}

export interface GeneratePostResponse {
  success: boolean;
  post_id: string;
  person_urn?: string;
  status: string;
  generated_content: string;
  slack_delivery?: unknown;
  message?: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch("/health");
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchLinkedInStatus(): Promise<LinkedInStatusResponse> {
  const response = await fetch("/linkedin/status");
  if (!response.ok) {
    throw new Error(`LinkedIn status check failed: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchPosts(): Promise<PostsResponse> {
  const response = await fetch("/posts");
  if (!response.ok) {
    throw new Error(`Failed to fetch posts: ${response.statusText}`);
  }
  return response.json();
}

export async function deletePost(postId: string): Promise<{ success: boolean; post_id: string; message: string }> {
  const response = await fetch(`/posts/${encodeURIComponent(postId)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete post: ${response.statusText}`);
  }
  return response.json();
}

export async function generatePost(topic: string): Promise<GeneratePostResponse> {
  const url = `/posts/generate?topic=${encodeURIComponent(topic)}`;
  const response = await fetch(url, {
    method: GENERATE_HTTP_METHOD,
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    let errorMsg = `Generation failed (${response.status})`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMsg = errorData.detail;
      }
    } catch {
      // fallback to status text
    }
    throw new Error(errorMsg);
  }

  return response.json();
}
