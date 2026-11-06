import http from "http";
import type { Duplex } from "stream";
import jwt, { type JwtPayload } from "jsonwebtoken";
import app from "../index";
import Client from "../config/prismaClient";
import { WebSocket, WebSocketServer, type RawData } from "ws";

const AUDIO_IN_FRAME = 0x01;

export const server = http.createServer(app);
const wss = new WebSocketServer({ noServer: true });
const connections = new WeakMap<
  WebSocket,
  { aiSocket: WebSocket; sessionId: string }
>();

function toBuffer(data: RawData): Buffer {
  if (Array.isArray(data)) return Buffer.concat(data);
  if (Buffer.isBuffer(data)) return data;
  return Buffer.from(data);
}

function reject(socket: Duplex, status: string) {
  socket.write(`HTTP/1.1 ${status}\r\n\r\n`);
  socket.destroy();
}

async function setStatus(sessionId: string, status: string) {
  try {
    await Client.interviewSession.update({
      where: { id: sessionId },
      data: { status: status as any },
    });
  } catch (error) {
    console.error(`Could not set session ${sessionId} to ${status}:`, error);
  }
}

async function persistEvent(sessionId: string, event: any) {
  try {
    if (event.type === "persist_plan") return;
    if (event.type === "persist_turn") {
      await Client.interviewTurn.create({
        data: {
          sessionId,
          idx: event.idx,
          role: event.role,
          text: event.text,
          tsMs: BigInt(Date.now()),
        },
      });
    }
  } catch (error) {
    console.error(
      `Could not persist ${event.type} for session ${sessionId}:`,
      error,
    );
  }
}

server.on("upgrade", (request, socket, head) => {
  authorizeAndConnect(request, socket, head).catch((error) => {
    console.error("Interview upgrade failed:", error);
    reject(socket, "500 Internal Server Error");
  });
});

async function authorizeAndConnect(
  request: http.IncomingMessage,
  socket: Duplex,
  head: Buffer,
) {
  const url = new URL(request.url ?? "/", "http://localhost");
  const pathname = url.pathname;
  if (!/^\/interview\/ws\/[^/]+$/.test(pathname))
    return reject(socket, "404 Not Found");

  const allowedOrigins = new Set(
    [
      "http://localhost:3000",
      "http://127.0.0.1:3000",
      "http://0.0.0.0:3000",
      "https://localhost:3000",
      "https://127.0.0.1:3000",
      "https://0.0.0.0:3000",
      ...(process.env.FRONTEND_ORIGIN || "")
        .split(",")
        .map((origin) => origin.trim())
        .filter(Boolean),
    ].filter(Boolean),
  );

  const requestOrigin = request.headers.origin;
  if (requestOrigin && !allowedOrigins.has(requestOrigin)) {
    return reject(socket, "403 Forbidden");
  }

  const tokenFromQuery = url.searchParams.get("token");
  const tokenFromCookie = request.headers.cookie
    ?.split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith("token="))
    ?.slice("token=".length);
  const token = tokenFromQuery ?? tokenFromCookie;

  console.log("WS upgrade token source:", {
    hasQueryToken: Boolean(tokenFromQuery),
    hasCookieToken: Boolean(tokenFromCookie),
    cookieHeaderPresent: Boolean(request.headers.cookie),
    requestUrl: request.url,
  });

  let userId: string;
  try {
    if (!token || !process.env.JWT_SECRET) throw new Error("Unauthorized");
    const payload = jwt.verify(
      decodeURIComponent(token),
      process.env.JWT_SECRET,
    ) as JwtPayload & { userid?: string; userId?: string; id?: string };

    const payloadUserId = payload.id ?? payload.userid ?? payload.userId;
    if (!payloadUserId) throw new Error("Token has no user id");
    userId = String(payloadUserId);
  } catch (error: any) {
    console.error("WS auth failed:", error?.message || error);
    return reject(socket, "401 Unauthorized");
  }
  const sessionId = decodeURIComponent(pathname.split("/").at(-1)!);
  const session = await Client.interviewSession.findFirst({
    where: { id: sessionId, userId },
  });

  if (!session) return reject(socket, "404 Not Found");
  if (session.status !== "created") return reject(socket, "409 Conflict");
  if (!session.resumeText) return reject(socket, "409 Conflict");

  const init = {
    type: "init",
    context: {
      resume_text: session.resumeText,
      jd_text: session.jd,
      position: session.position,
      company_name: session.companyName,
      difficulty: session.difficulty,
      interview_type: session.interviewType,
      focus_areas: session.focusAreas,
      duration_minutes: session.duration,
    },
  };

  const aiEngineBaseUrl = (
    process.env.AI_ENGINE_WS_URL ?? "ws://127.0.0.1:8000/interview/ws"
  ).replace(/\/$/, "");

  const aiSocket = new WebSocket(
    `${aiEngineBaseUrl}/${encodeURIComponent(sessionId)}`,
  );

  let handshakeHandled = false;

  aiSocket.once("open", () => {
    handshakeHandled = true;
    aiSocket.send(JSON.stringify(init));
    wss.handleUpgrade(request, socket, head, (clientSocket) => {
      connections.set(clientSocket, { aiSocket, sessionId });
      wss.emit("connection", clientSocket, request);
    });
  });

  aiSocket.once("error", (error) => {
    console.error(
      "Could not connect to AI interview WebSocket:",
      error.message,
    );
    if (!handshakeHandled) {
      handshakeHandled = true;
      reject(socket, "502 Bad Gateway");
    }
  });
}

wss.on("connection", (ws) => {
  const connection = connections.get(ws);
  if (!connection) {
    ws.close(1011, "AI interview socket was not initialized");
    return;
  }

  const { aiSocket, sessionId } = connection;

  let started = false;
  let ended = false;
  let finalized = false;

  const finalize = () => {
    if (finalized) return;
    finalized = true;
    if (started && !ended) void setStatus(sessionId, "abandoned");
  };

  ws.on("message", (data, isBinary) => {
    if (!isBinary) {
      if (aiSocket.readyState === WebSocket.OPEN)
        aiSocket.send(data.toString());
      return;
    }

    const frame = toBuffer(data);
    if (frame.byteLength < 2 || frame[0] !== AUDIO_IN_FRAME) {
      ws.send(
        JSON.stringify({
          type: "error",
          detail: "Unsupported or empty audio frame.",
        }),
      );
      return;
    }

    console.log(
      `Node forwarded audio frame: session=${sessionId}, bytes=${frame.byteLength}`,
    );

    if (aiSocket.readyState === WebSocket.OPEN) {
      aiSocket.send(frame, { binary: true });
    } else {
      ws.send(
        JSON.stringify({
          type: "error",
          detail: "AI interview socket is disconnected.",
        }),
      );
    }
  });

  aiSocket.on("message", (data, isBinary) => {
    if (ws.readyState !== WebSocket.OPEN) return;

    if (isBinary) {
      ws.send(toBuffer(data), { binary: true });
      return;
    }

    const text = data.toString();
    let event: any = null;
    try {
      event = JSON.parse(text);
    } catch {
      // not JSON
    }

    if (
      event &&
      typeof event.type === "string" &&
      event.type.startsWith("persist_")
    ) {
      if (event.type === "persist_plan") {
        started = true;
        void setStatus(sessionId, "in_progress");
      }
      void persistEvent(sessionId, event);
      return;
    }

    if (event?.type === "ended") {
      ended = true;
      void setStatus(sessionId, "completed");
    }

    ws.send(text);
  });

  aiSocket.on("close", (code, reason) => {
    if (ws.readyState === WebSocket.OPEN) {
      const clientCode =
        code === 1000 || (code >= 4000 && code <= 4999) ? code : 1011;
      ws.close(clientCode, "AI interview socket closed");
    }
    finalize();
  });

  ws.on("close", (code, reason) => {
    if (
      aiSocket.readyState === WebSocket.OPEN ||
      aiSocket.readyState === WebSocket.CONNECTING
    ) {
      aiSocket.close();
    }
    finalize();
  });

  ws.on("error", (error) => {
    console.error("Client websocket error:", error);
  });
});
