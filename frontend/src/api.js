// Central API base configuration
// In dev, CRA proxy (package.json#proxy) maps '/api' to backend
// In production (Docker), frontend and backend share the same origin
export const API_BASE = process.env.REACT_APP_API_BASE || '/api';

