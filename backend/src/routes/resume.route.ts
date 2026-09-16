import Router from "express";
import { uploadResume } from "../controllers/resume.controller";
import multer from "../middleware/multer.middleware";
import { authMiddleware } from "../middleware/auth.middleware";

const resumeRouter = Router();

resumeRouter.post(
  "/resume",
  authMiddleware,
  multer.single("resume"),
  uploadResume,
);

export default resumeRouter;
