import { Router } from "express";
import { authMiddleware } from "../middleware/auth.middleware";
import tailorResumeResult from "../controllers/tailorResume.controller";
import tailorResumeEventStream from "../controllers/tailorResumeEventStream.controller";
import { wokerMiddlewareSecret } from "../middleware/worker.middleware";
const tailorRouter = Router();

tailorRouter.post(
  "/tailor_resume_callback",
  wokerMiddlewareSecret,
  tailorResumeResult,
);
tailorRouter.get("/stream-status/:id", authMiddleware, tailorResumeEventStream);

export default tailorRouter;
