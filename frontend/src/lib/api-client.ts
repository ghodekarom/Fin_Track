import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor to format error shapes
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // If backend returns custom validation details (e.g. from Pydantic)
    // we extract them so the UI can print structured messages.
    const message =
      error.response?.data?.detail ||
      error.message ||
      "An unexpected error occurred.";
    
    // Create a normalized error object
    const normalizedError = {
      message: typeof message === "string" ? message : JSON.stringify(message),
      raw: error.response?.data,
      status: error.response?.status,
    };
    
    return Promise.reject(normalizedError);
  }
);
