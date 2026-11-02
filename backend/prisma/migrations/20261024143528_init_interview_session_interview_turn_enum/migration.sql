-- CreateEnum
CREATE TYPE "SessionStatus" AS ENUM ('created', 'in_progress', 'completed', 'abandoned');

-- CreateEnum
CREATE TYPE "TurnRole" AS ENUM ('agent', 'user');

-- CreateEnum
CREATE TYPE "InterviewType" AS ENUM ('technical', 'behavioral', 'mixed');

-- CreateEnum
CREATE TYPE "Difficulty" AS ENUM ('junior', 'mid', 'senior');

-- CreateTable
CREATE TABLE "InterviewSession" (
    "id" TEXT NOT NULL,
    "position" TEXT NOT NULL,
    "difficulty" "Difficulty" NOT NULL,
    "jd" TEXT NOT NULL,
    "resumeText" TEXT NOT NULL,
    "interviewType" "InterviewType" NOT NULL,
    "status" "SessionStatus" NOT NULL DEFAULT 'created',
    "duration" INTEGER NOT NULL,
    "recordingUrl" TEXT,
    "startedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "endedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "userId" TEXT NOT NULL,
    "resumeId" TEXT,

    CONSTRAINT "InterviewSession_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "InterviewTurn" (
    "id" BIGSERIAL NOT NULL,
    "sessionId" TEXT NOT NULL,
    "idx" INTEGER NOT NULL,
    "role" "TurnRole" NOT NULL,
    "text" TEXT NOT NULL,
    "wasInterrupted" BOOLEAN NOT NULL DEFAULT false,
    "tsMs" BIGINT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "InterviewTurn_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "InterviewSession_userId_idx" ON "InterviewSession"("userId");

-- CreateIndex
CREATE INDEX "InterviewTurn_sessionId_idx" ON "InterviewTurn"("sessionId");

-- CreateIndex
CREATE INDEX "Resume_userId_idx" ON "Resume"("userId");

-- AddForeignKey
ALTER TABLE "InterviewSession" ADD CONSTRAINT "InterviewSession_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewSession" ADD CONSTRAINT "InterviewSession_resumeId_fkey" FOREIGN KEY ("resumeId") REFERENCES "Resume"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterviewTurn" ADD CONSTRAINT "InterviewTurn_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "InterviewSession"("id") ON DELETE CASCADE ON UPDATE CASCADE;
