import { Request, Response } from "express";
import { Router } from "express";
import tailorResumeResult from "../controllers/tailorResume.controller";
const tailorRouter = Router();

tailorRouter.post("/tailor_resume_callback", tailorResumeResult);

export default tailorRouter;
