/**
 * MeetLoop API Client
 * Seamlessly handles both local Vite proxy (/api) and production backend URL (VITE_API_URL).
 */

const BASE_URL = import.meta.env.VITE_API_URL || '';

export async function runAgent(payload) {
  const url = BASE_URL ? `${BASE_URL.replace(/\/$/, '')}/run` : '/api/run';
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Agent run failed (${response.status}): ${errorText || response.statusText}`);
  }

  return response.json();
}

export async function checkHealth() {
  const url = BASE_URL ? `${BASE_URL.replace(/\/$/, '')}/health` : '/api/health';
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return response.json();
}

export async function getFixtures() {
  const url = BASE_URL ? `${BASE_URL.replace(/\/$/, '')}/fixtures` : '/api/fixtures';
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load fixtures (${response.status})`);
  }
  return response.json();
}
