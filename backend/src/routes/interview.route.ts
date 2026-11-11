import { Router } from "express";
import { authMiddleware } from "../middleware/auth.middleware";
import multer from "../middleware/multer.middleware";
import { mockInterview } from "../controllers/mockInterview.controller";
import {
  closeWebRTCPeer,
  getWebRTCSignal,
  postWebRTCSignal,
} from "../controllers/interviewWebRTC.controller";

const interviewRouter = Router();

interviewRouter.post(
  "/mock-interview",
  authMiddleware,
  multer.single("resume"),
  mockInterview,
);

interviewRouter.post("/webrtc/signal", authMiddleware, postWebRTCSignal);
interviewRouter.get("/webrtc/signal", authMiddleware, getWebRTCSignal);
interviewRouter.post("/webrtc/close", authMiddleware, closeWebRTCPeer);

export default interviewRouter;
