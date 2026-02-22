/**
 * Base API client configuration.
 *
 * All backend requests go through this client.
 * The Vite dev server proxies /api to the backend,
 * so we use relative URLs.
 */

import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});