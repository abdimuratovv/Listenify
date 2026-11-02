let csrf = "";
export function setCsrf(value: string) {
  csrf = value;
}
export function cancelAttempt(id: string) {
  // A keepalive request can complete after a page navigation. Expiry and a new
  // attempt provide the server-side fallback if the browser cannot send it.
  void fetch(`/api/attempts/${encodeURIComponent(id)}/cancel`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-CSRFToken": csrf },
    keepalive: true,
  }).catch(() => {});
}
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function api<T = any>(
  path: string,
  method = "GET",
  data?: unknown,
): Promise<T> {
  const form = data instanceof FormData;
  const response = await fetch(`/api/${path}`, {
    method,
    credentials: "same-origin",
    headers: {
      ...(method !== "GET" ? { "X-CSRFToken": csrf } : {}),
      ...(!form && data !== undefined
        ? { "Content-Type": "application/json" }
        : {}),
    },
    body: data === undefined ? undefined : form ? data : JSON.stringify(data),
  });
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("auth/"))
      window.dispatchEvent(new Event("session-expired"));
    throw new ApiError(result.error || "So‘rov bajarilmadi.", response.status);
  }
  if (result.csrf) setCsrf(result.csrf);
  return result;
}
