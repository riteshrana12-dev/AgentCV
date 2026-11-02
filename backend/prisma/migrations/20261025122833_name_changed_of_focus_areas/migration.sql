/*
  Warnings:

  - You are about to drop the column `focus_areas` on the `InterviewSession` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "InterviewSession" DROP COLUMN "focus_areas",
ADD COLUMN     "focusAreas" TEXT;
