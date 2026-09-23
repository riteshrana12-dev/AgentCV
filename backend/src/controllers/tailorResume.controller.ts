import { Request, Response } from "express";
import { z } from "zod";
import client from "../config/prismaClient";

const tailorResumeSchema = z.object({
  resume_id: z.string(),
  ats_score: z.number(),
  tailored_ats_score: z.number(),
  score_breakdown: z.record(z.string(), z.number()),
  tailored_score_breakdown: z.record(z.string(), z.number()),
  matched_skills: z.array(z.string()),

  // Missing skills is a dict with two arrays
  missing_skills: z.object({
    truly_missing: z.array(z.string()),
    partially_supported: z.array(
      z.object({
        skill: z.string(),
        related_experience: z.string(),
        gap: z.string(),
      }),
    ),
  }),

  // Weak verbs are structured objects
  weak_verbs: z.array(
    z.object({
      verb: z.string(),
      suggested_alternatives: z.array(z.string()),
    }),
  ),

  formatting_alerts: z.array(z.string()),
  requirement_analysis: z.array(
    z.object({
      requirement: z.string(),

      category: z.string(),

      importance: z.string(),

      candidate_match: z.string(),

      evidence_from_resume: z.array(z.string()),
    }),
  ),
  experience_evidence: z.array(
    z.object({
      source: z.string(),

      relevant_requirement: z.string(),

      evidence: z.string(),

      relevance_score: z.number(),
    }),
  ),

  curation_signals: z.object({
    top_requirements: z.array(z.string()),

    strongest_candidate_evidence: z.array(z.string()),

    best_projects_to_highlight: z.array(z.string()),

    transferable_skills: z.array(
      z.object({
        jd_requirement: z.string(),

        candidate_skill: z.string(),

        reason: z.string(),
      }),
    ),

    skills_or_experiences_to_avoid_highlighting: z.array(z.string()),
  }),
  strategic_recommendation: z.string(),
  tailored_bullets: z.array(z.string()),
  project_recommendation_type: z.string(),
  project_advice_message: z.string(),
  cover_letter: z.string(),
  cold_email: z.string(),
  linkedin_message: z.string(),
  generated_docx_url: z.string().url(),
  generated_pdf_url: z.string().url(),
});

const tailorResumeResult = async (req: Request, res: Response) => {
  try {
    console.log("result from tailored resume controller side:  ", req);
    const parseResult = tailorResumeSchema.safeParse(req.body);

    if (!parseResult.success) {
      console.error("Validation failed:", parseResult.error.format());
      return res.status(400).json({ error: "Invalid payload" });
    }

    console.log("parsedResult  :", parseResult.data);
    const {
      resume_id,
      ats_score,
      tailored_ats_score,
      tailored_score_breakdown,
      score_breakdown,
      matched_skills,
      missing_skills,
      weak_verbs,
      formatting_alerts,
      requirement_analysis,
      experience_evidence,
      curation_signals,
      strategic_recommendation,
      tailored_bullets,
      project_recommendation_type,
      project_advice_message,
      cover_letter,
      cold_email,
      linkedin_message,
      generated_docx_url,
      generated_pdf_url,
    } = parseResult.data;

    await client.resume.update({
      where: { id: resume_id },
      data: {
        atsScore: ats_score,
        tailoredAtsScore: tailored_ats_score,
        tailoredResumeUrlPdf: generated_pdf_url,
        tailoreResumeUrlDocx: generated_docx_url,
      },
    });

    console.info("Resume updated with tailoring result:", resume_id);

    await client.suggestion.upsert({
      where: { resumeId: resume_id },
      update: {
        coverLetter: cover_letter,
        coldEmail: cold_email,
        linkedinMessage: linkedin_message,
        tailoredBulletsPoints: tailored_bullets,
        projectRecommendation: project_recommendation_type,
        projectSuggestionAdvice: project_advice_message,
        matchedSkills: matched_skills,
        missingSkills: missing_skills,
      },
      create: {
        resumeId: resume_id,
        coverLetter: cover_letter,
        coldEmail: cold_email,
        linkedinMessage: linkedin_message,
        tailoredBulletsPoints: tailored_bullets,
        projectRecommendation: project_recommendation_type,
        projectSuggestionAdvice: project_advice_message,
        matchedSkills: matched_skills,
        missingSkills: missing_skills,
      },
    });

    return res.status(200).json({
      success: true,
      data: {
        ats_score,
        tailored_ats_score,
        tailored_score_breakdown,
        score_breakdown,
        matched_skills,
        missing_skills,
        weak_verbs,
        formatting_alerts,
        tailored_bullets,
        requirement_analysis,
        experience_evidence,
        curation_signals,
        strategic_recommendation,
        project_recommendation_type,
        project_advice_message,
        cover_letter,
        cold_email,
        linkedin_message,
        generated_docx_url,
        generated_pdf_url,
      },
    });
  } catch (err: any) {
    if (err instanceof Error) {
      console.error("Validation failed:", err.message);
    }
    return res
      .status(400)
      .json({ error: "Invalid payload", details: err.errors ?? err });
  }
};

export default tailorResumeResult;
