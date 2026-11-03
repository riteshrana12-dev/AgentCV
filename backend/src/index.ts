import "dotenv/config";
import express from "express";
import cors from "cors";
import helmet from "helmet";
import cookieParser from "cookie-parser";
import morgan from "morgan";

import resumeRouter from "./routes/resume.route";
import authRouter from "./routes/auth.route";
import tailorRouter from "./routes/jobCallback.route";
import interviewRouter from "./routes/interview.route";

const app = express();

app.use(helmet());

const allowedOrigins = (
  process.env.FRONTEND_ORIGIN || "http://localhost:3000"
)
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

app.use(
  cors({
    origin: (origin, callback) => {
      if (!origin || allowedOrigins.includes(origin)) {
        callback(null, true);
        return;
      }
      callback(new Error("Not allowed by CORS"));
    },
    credentials: true,
  }),
);

app.use(express.json());
app.use(morgan("dev"));
app.use(cookieParser());

app.use("/api/v1/auth", authRouter);
app.use("/api/v1/upload", resumeRouter);
app.use("/api/v1/resume", tailorRouter);
app.use("/api/v1/interview", interviewRouter);

export default app;
