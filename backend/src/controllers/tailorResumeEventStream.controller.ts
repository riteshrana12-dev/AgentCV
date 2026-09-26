import { Request, Response } from "express";
import Client from "../config/prismaClient";

const tailorResumeEventStream = async (req: Request, res: Response) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");

  try {
    const resumeId = req.params.id;
    res.write(`data: ${JSON.stringify({ status: "connected" })}\n\n`);
    const interval = setInterval(async () => {
      const resume = await Client.resume.findUnique({
        where: { id: resumeId as string },
        include: {
          suggestion: {
            select: {
              id: true,
              coverLetter: true,
              linkedinMessage: true,
              tailoredBulletsPoints: true,
              projectRecommendation: true,
              projectSuggestionAdvice: true,
              matchedSkills: true,
              missingSkills: true,
            },
          },
        },
      });
      if (resume?.status === "finished") {
        res.write(`data: ${JSON.stringify(resume)}\n\n`);

        clearInterval(interval);
        res.end();
      }
    }, 3000);
    req.on("close", () => {
      clearInterval(interval);
      res.end();
    });
    return;
  } catch (error: any) {
    return res.status(500).json({
      success: false,
      message: "Error streaming the event for resume",
      errro: error.message,
    });
  }
};

export default tailorResumeEventStream;
