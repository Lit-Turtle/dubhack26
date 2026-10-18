const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, options);
  } catch {
    throw new Error('Cannot reach the backend. Check that it is running and that the API URL is correct.');
  }
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error(`The API returned an unexpected response (${response.status}). Check the backend deployment and API URL.`);
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === 'string' ? error.detail : `Request failed (${response.status})`);
  }
  return response.json();
}

export function detectIngredients(file) {
  if (file.size > 4 * 1024 * 1024) {
    throw new Error('Choose a photo smaller than 4 MB for upload.');
  }
  const body = new FormData();
  body.append('image', file);
  return request('/detect', { method: 'POST', body });
}

export function getRecipes(input) {
  return request('/recipes', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input),
  });
}
