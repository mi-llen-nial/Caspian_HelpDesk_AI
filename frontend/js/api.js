const API_BASE_URL = `${window.location.origin}/api/v1`;

async function apiGet(path) {
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Ошибка запроса: ${res.status}`);
  }
  return res.json();
}

async function apiPost(path, data) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Ошибка запроса: ${res.status} ${text}`);
  }
  return res.json();
}

