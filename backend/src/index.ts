import "dotenv/config";
import express from "express";
import cors from "cors";
import helmet from "helmet";
import cookieParser from "cookie-parser";
import morgan from "morgan";

import resumeRouter from "./routes/resume.route";
import authRouter from "./routes/auth.route";
import tailorRouter from "./routes/jobCallback.route";

const app = express();

app.use(helmet());

app.use(
  cors({
    origin: process.env.FRONTEND_ORIGIN || "http://localhost:3000",
    credentials: true,
  }),
);

app.use(express.json());
app.use(morgan("dev"));
app.use(cookieParser());

app.use("/api/v1/auth", authRouter);
app.use("/api/v1/upload", resumeRouter);
app.use("/api/v1/resume", tailorRouter);

export default app;
