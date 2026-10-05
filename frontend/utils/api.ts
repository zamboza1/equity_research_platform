import axios from 'axios';
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((item) => `${(item.loc || []).slice(1).join('.')}: ${item.msg}`).join('; ');
    if (error.code === 'ECONNABORTED') return 'The request timed out. Retry or use manual inputs.';
    if (!error.response) return 'Cannot reach the research API. Check that the backend is running.';
  }
  return error instanceof Error ? error.message : 'The request could not be completed.';
}
const api = axios.create({ baseURL: '/api', timeout: 30000 });
api.interceptors.response.use(response => response, error => {
  // Existing screens expect a printable detail; Pydantic returns an array.
  if (error.response?.data && typeof error.response.data === 'object') {
    error.response.data.detail = errorMessage(error);
  }
  return Promise.reject(error);
});
export default api;
