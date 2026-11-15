import http from "http";
import app from "../index";

// Browser audio now uses WebRTC. The Node-to-Python interview bridge is managed
// per session in src/webrtc/peerManager.ts and does not upgrade this HTTP server.
export const server = http.createServer(app);
