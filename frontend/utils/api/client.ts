import axios from "axios";

// API base URL - FastAPI backend (deployed)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://backend-service-484671782718.us-east1.run.app";

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Important: sends cookies with every request
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor for handling auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // User is not authenticated - could redirect to login
      console.warn("Unauthorized - user may need to log in");
      // Optionally: window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

// Helper to get base URL (for backward compatibility)
export function getApiBaseUrl() {
  return API_BASE_URL;
}