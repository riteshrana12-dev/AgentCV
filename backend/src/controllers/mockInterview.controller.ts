import { Request, Response } from "express";
import { success, z } from "zod";
import FormData from "form-data";
import api from "../config/api";
import Client from "../config/prismaClient";

const mockInterviewSchema = z.object({
  companyName: z.string().min(2).max(100),

  position: z.string().min(2).max(100),

  difficulty: z.enum(["junior", "mid", "senior"]),

  interviewType: z.enum(["technical", "behavioral", "mixed"]),

  focusAreas: z.string().max(500),

  duration: z.coerce.number().min(10).max(20),

  jd: z.string().min(200).max(5000),
});

export const mockInterview = async (req: Request, res: Response) => {
  const formData = new FormData();

  try {
    console.log("Body:  ", req.body);
    const parsedData = mockInterviewSchema.safeParse({
      ...req.body,
      duration: Number(req.body.duration),
    });
    if (!parsedData.success) {
      return res.status(400).json({ error: parsedData.error.issues });
    }

    const file = req.file;
    if (!file) {
      return res.status(400).json({
        success: false,
        message: "No file uploaded",
      });
    }

    const {
      companyName,
      position,
      difficulty,
      interviewType,
      duration,
      jd,
      focusAreas,
    } = parsedData.data;

    const interviewSession = await Client.interviewSession.create({
      data: {
        userId: req.userId!,
        companyName: companyName,
        position: position,
        difficulty: difficulty,
        resumeText: "",
        jd: jd,
        interviewType: interviewType,
        focusAreas: focusAreas,
        duration: duration,
        status: "created",
      },
    });

    if (!interviewSession.id) {
      return res.status(400).json({
        success: false,
        message: "Trouble in creating interview Session",
      });
    }

    formData.append("resume", file.buffer, {
      filename: file.originalname,
      contentType: file.mimetype,
    });

    formData.append("jd", jd);
    formData.append("sessionId", interviewSession.id);

    const sessionContext = await api.post(
      "/interview/create-session",
      formData,
      {
        headers: formData.getHeaders(),
      },
    );

    const { sessionId, resumeText, parseJd } = sessionContext.data;

    await Client.interviewSession.update({
      where: { id: sessionId },
      data: { resumeText: resumeText, jd: parseJd },
    });

    return res.status(200).json({
      sessionId: sessionId,
      success: true,
      message: "Session Context creation is successfull ",
    });
  } catch (error: any) {
    console.error("Error uploading resume:", error);

    const apiErrorDetail =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.response?.data?.error ||
      error?.message ||
      "Unknown error";

    const statusCode = error?.response?.status || 500;

    return res.status(statusCode).json({
      success: false,
      message: "Error uploading resume",
      error: apiErrorDetail,
    });
  }
};
