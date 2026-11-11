import type { Request, Response } from "express";
import { z } from "zod";
import FormData from "form-data";
import api from "../config/api";
import Client from "../config/prismaClient";

const interviewSessionSchema = z.object({
  companyName: z.string().min(2).max(100),
  position: z.string().min(2).max(100),
  difficulty: z.enum(["junior", "mid", "senior"]),
  interviewType: z.enum(["technical", "behavioral", "mixed"]),
  focusAreas: z.string().max(500).default(""),
  duration: z.coerce.number().min(10).max(60),
  jd: z.string().min(200).max(5000),
});

export const mockInterview = async (req: Request, res: Response) => {
  const parsedData = interviewSessionSchema.safeParse({
    ...req.body,
    duration: Number(req.body.duration),
  });

  if (!parsedData.success) {
    return res.status(400).json({
      success: false,
      message: "Invalid interview session payload.",
      error: parsedData.error.issues,
    });
  }

  const file = req.file;
  if (!file) {
    return res.status(400).json({
      success: false,
      message: "No file uploaded.",
    });
  }

  try {
    const data = parsedData.data;
    const session = await Client.interviewSession.create({
      data: {
        userId: req.userId!,
        companyName: data.companyName,
        position: data.position,
        difficulty: data.difficulty,
        resumeText: "",
        jd: data.jd,
        interviewType: data.interviewType,
        focusAreas: data.focusAreas,
        duration: data.duration,
        status: "created",
      },
    });

    const formData = new FormData();
    formData.append("resume", file.buffer, {
      filename: file.originalname,
      contentType: file.mimetype,
    });
    formData.append("jd", data.jd);
    formData.append("sessionId", session.id);

    const response = await api.post("/interview/create-session", formData, {
      headers: formData.getHeaders(),
    });
    const aiContext = response.data as {
      resumeText: string;
      parseJd: string;
    };

    await Client.interviewSession.update({
      where: { id: session.id },
      data: { resumeText: aiContext.resumeText, jd: aiContext.parseJd },
    });

    return res.status(200).json({
      success: true,
      sessionId: session.id,
      message: "Session Context creation is successful.",
    });
  } catch (error: any) {
    const detail =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.response?.data?.error ||
      error?.message ||
      "Unknown error";

    return res.status(error?.response?.status || 500).json({
      success: false,
      message: "Error uploading resume",
      error: detail,
    });
  }
};
