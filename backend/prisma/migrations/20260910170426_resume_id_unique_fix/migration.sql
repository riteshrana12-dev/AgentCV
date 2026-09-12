/*
  Warnings:

  - A unique constraint covering the columns `[resumeId]` on the table `Suggestion` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "Suggestion_resumeId_key" ON "Suggestion"("resumeId");
