import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

const UNSAFE_METHODS = new Set(["post", "put", "patch", "delete"]);

// Django's SessionAuthentication requires the csrftoken cookie to be echoed
// back as the X-CSRFToken header on every unsafe request.
api.interceptors.request.use(async (config) => {
  if (UNSAFE_METHODS.has((config.method || "").toLowerCase())) {
    let token = getCookie("csrftoken");
    if (!token) {
      await api.get("/auth/csrf/");
      token = getCookie("csrftoken");
    }
    if (token) {
      config.headers["X-CSRFToken"] = token;
    }
  }
  return config;
});

export function getErrorMessage(error) {
  if (!error.response) {
    return "Network error — unable to reach the server.";
  }

  const { status, data } = error.response;

  if (data) {
    if (typeof data.message === "string") return data.message;
    if (typeof data.detail === "string") return data.detail;
    if (typeof data === "string") return data;
    const firstField = Object.values(data)[0];
    if (Array.isArray(firstField) && firstField.length) return firstField[0];
  }

  switch (status) {
    case 400:
      return "The request was invalid.";
    case 401:
      return "Invalid username or password.";
    case 403:
      return "You do not have permission to do that.";
    case 404:
      return "The requested resource was not found.";
    case 500:
      return "Something went wrong on the server. Please try again later.";
    default:
      return "An unexpected error occurred.";
  }
}

export default api;
