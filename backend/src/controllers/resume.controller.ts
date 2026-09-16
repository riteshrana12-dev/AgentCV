import { Request, Response } from "express";
import { v4 as uuid } from "uuid";
import supabase from "../config/supabase";
import Client from "../config/prismaClient";
import api from "../config/api";
import { z } from "zod";

const uploadResumeSchema = z.object({
  jd: z.string().max(3000).min(200),
  github_username: z.string().max(100).optional(),
});

export const uploadResume = async (req: Request, res: Response) => {
  try {
    const parsedData = uploadResumeSchema.safeParse(req.body);

    if (!parsedData.success) {
      return res.status(400).json({ error: parsedData.error.issues });
    }

    const { jd, github_username } = parsedData.data;

    const file = req.file;
    if (!file) {
      return res.status(400).json({
        success: false,
        message: "No file uploaded",
      });
    }

    const fileName = `original/${uuid()}-${file.originalname}`;
    const { data, error } = await supabase.storage
      .from("resumes")
      .upload(fileName, file.buffer, { contentType: file.mimetype });

    if (error) {
      return res.status(400).json({
        success: false,
        message: error.message,
      });
    }

    const uploadedResumePath = supabase.storage
      .from("resumes")
      .getPublicUrl(fileName).data.publicUrl;

    const resume = await Client.resume.create({
      data: {
        userId: req.userId!,
        originalResumePath: fileName,
        originalResumeUrl: uploadedResumePath,
        fileName: file.originalname,
        fileSize: file.size,
        fileType: file.mimetype,
        jd,
        tailoredResumeUrlPdf: "",
        tailoreResumeUrlDocx: "",
        atsScore: 0,
        tailoredAtsScore: 0,
      },
    });

    const response = await api.post("/resume/tailor_resume", {
      storage_path: fileName,
      file_name: file.originalname,
      jd,
      github_username,
      resume_id: resume.id,
      callback_url: `${process.env.NODEJS_HOST}/api/v1/resume/tailor_resume_callback`,
    });

    console.log("response in nodejs side   :", response);

    return res.status(202).json({
      success: true,
      message: "Resume accepted and tailoring has been queued.",
      data: {
        resumeId: resume.id,
        originalResumeUrl: uploadedResumePath,
      },
    });
  } catch (error: any) {
    console.error("Error uploading resume:", error);
    return res.status(500).json({
      success: false,
      message: "Error uploading resume",
      errro: error.message,
    });
  }
};
