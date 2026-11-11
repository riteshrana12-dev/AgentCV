import type { Request, Response } from "express";
import Client from "../config/prismaClient";
import { clearWebRTCSignals, getWebRTCSignals } from "../webrtc/signalStore";
import { handleWebRTCSignal } from "../webrtc/peerManager";

export const postWebRTCSignal = async (req: Request, res: Response) => {
  const { sessionId, peerId, type, payload } = req.body ?? {};

  if (!sessionId || !peerId || !type) {
    return res.status(400).json({
      message: "sessionId, peerId, and type are required.",
    });
  }

  if (!["offer", "answer", "candidate"].includes(type)) {
    return res.status(400).json({ message: "Unsupported WebRTC signal type." });
  }

  const interviewSession = await Client.interviewSession.findFirst({
    where: {
      id: String(sessionId),
      userId: req.userId!,
    },
  });

  if (!interviewSession) {
    return res.status(404).json({ message: "Interview session not found." });
  }
  if (
    interviewSession.status === "completed" ||
    interviewSession.status === "abandoned"
  ) {
    return res
      .status(409)
      .json({ message: "This interview session is already closed." });
  }
  if (!interviewSession.resumeText) {
    return res
      .status(409)
      .json({ message: "Interview resume context is not ready." });
  }

  try {
    await handleWebRTCSignal(
      String(sessionId),
      String(peerId),
      type,
      payload ?? null,
      {
        resumeText: interviewSession.resumeText,
        jd: interviewSession.jd,
        position: interviewSession.position,
        companyName: interviewSession.companyName,
        difficulty: interviewSession.difficulty,
        interviewType: interviewSession.interviewType,
        focusAreas: interviewSession.focusAreas,
        duration: interviewSession.duration,
      },
    );

    return res.json({
      ok: true,
      sessionId: String(sessionId),
      peerId: String(peerId),
      type,
    });
  } catch (error) {
    return res.status(400).json({
      message:
        error instanceof Error
          ? error.message
          : "Invalid WebRTC signal payload.",
    });
  }
};

export const getWebRTCSignal = async (req: Request, res: Response) => {
  const sessionId = req.query.sessionId;
  const peerId = req.query.peerId;

  if (!sessionId) {
    return res.status(400).json({ message: "sessionId is required." });
  }

  const interviewSession = await Client.interviewSession.findFirst({
    where: {
      id: String(sessionId),
      userId: req.userId!,
    },
  });

  if (!interviewSession) {
    return res.status(404).json({ message: "Interview session not found." });
  }

  const signals = getWebRTCSignals(
    String(sessionId),
    peerId ? String(peerId) : undefined,
  );

  if (peerId) {
    clearWebRTCSignals(String(sessionId), String(peerId));
  }

  return res.json({ signals });
};
