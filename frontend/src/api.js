const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === 'string' ? error.detail : `Request failed (${response.status})`);
  }
  return response.json();
}

export function detectIngredients(file) {
  const body = new FormData();
  body.append('image', file);
  return request('/detect', { method: 'POST', body });
}

export function getRecipes(input) {
  return request('/recipes', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input),
  });
}
