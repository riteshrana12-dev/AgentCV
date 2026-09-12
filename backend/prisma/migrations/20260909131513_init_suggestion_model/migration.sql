-- CreateTable
CREATE TABLE "Suggestion" (
    "id" TEXT NOT NULL,
    "coverLetter" TEXT NOT NULL,
    "coldEmail" TEXT NOT NULL,
    "linkedinMessage" TEXT NOT NULL,
    "tailoredBulletsPoints" TEXT NOT NULL,
    "projectRecommendation" TEXT NOT NULL,
    "projectSuggestionAdvice" TEXT NOT NULL,
    "matchedSkills" TEXT NOT NULL,
    "missingSkills" TEXT NOT NULL,
    "resumeId" TEXT NOT NULL,

    CONSTRAINT "Suggestion_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "Suggestion" ADD CONSTRAINT "Suggestion_resumeId_fkey" FOREIGN KEY ("resumeId") REFERENCES "Resume"("id") ON DELETE CASCADE ON UPDATE CASCADE;
