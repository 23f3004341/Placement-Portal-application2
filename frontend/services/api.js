// Central helper for every backend call. Sends the session cookie, normalises
// the request body, and turns any error response into a thrown Error so views
// can simply try/catch.
async function apiRequest(path, options = {}) {
  const config = {
    credentials: "same-origin", // send the Flask-Login session cookie
    ...options,
    headers: { ...(options.headers || {}) },
  };
  // JSON bodies are stringified; FormData (e.g. resume upload) is sent as-is so
  // the browser can set the multipart boundary itself.
  if (config.body && !(config.body instanceof FormData)) {
    config.headers["Content-Type"] = "application/json";
    config.body = JSON.stringify(config.body);
  }

  const response = await fetch(path, config);
  const payload = await response
    .json()
    .catch(() => ({ ok: false, message: "Invalid server response." }));

  // Treat both HTTP errors and {ok:false} API responses as failures.
  if (!response.ok || payload.ok === false) {
    const error = new Error(payload.message || `Request failed (${response.status})`);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

window.apiRequest = apiRequest;
