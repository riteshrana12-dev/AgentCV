import { Router } from "express";
import { authMiddleware } from "../middleware/auth.middleware";
import multer from "../middleware/multer.middleware";
import { mockInterview } from "../controllers/mockInterview.controller";

const interviewRouter = Router();

interviewRouter.post(
  "/mock-interview",
  authMiddleware,
  multer.single("resume"),
  mockInterview,
);

export default interviewRouter;
