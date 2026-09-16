import axios from "axios";

const api = axios.create({
  baseURL: process.env.FASTAPI_HOST || "http://localhost:8000",

  withCredentials: true, // Include cookies in requests
});

export default api;
