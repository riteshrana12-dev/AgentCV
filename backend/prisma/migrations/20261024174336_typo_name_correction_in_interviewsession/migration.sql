/*
  Warnings:

  - You are about to drop the column `focus_area` on the `InterviewSession` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "InterviewSession" DROP COLUMN "focus_area",
ADD COLUMN     "focus_areas" TEXT;
