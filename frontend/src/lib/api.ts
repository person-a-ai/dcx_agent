const API = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json();
}

// Sessions
export const getSession = (sid: string) => request<{ status: string; data: Record<string, unknown> }>(`/session/${sid}`);
export const saveSession = (sid: string, data: Record<string, unknown>) =>
  request("/save-session", { method: "POST", body: JSON.stringify({ sid, data }) });

// Chat
export const sendChat = (body: Record<string, unknown>) =>
  request<{ status: string; answer: string; sources: Record<string, unknown>[]; added_keywords?: string[] }>("/chat", { method: "POST", body: JSON.stringify(body) });
export const sendInsightChat = (body: Record<string, unknown>) =>
  request<{ status: string; answer: string; modified: boolean; sources: Record<string, unknown>[] }>("/insight-chat", { method: "POST", body: JSON.stringify(body) });
