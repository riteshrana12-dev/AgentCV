import http from "http";
import app from "../index";
import { WebSocketServer } from "ws";
export const server = http.createServer(app);

const wss = new WebSocketServer({ server });

wss.on("connection", (ws) => {
  console.log("Client connected");
  ws.send("hello to web socket and nodejs server");
});
