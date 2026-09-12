/*
  Warnings:

  - You are about to drop the column `generatedDocxUrl` on the `Resume` table. All the data in the column will be lost.
  - You are about to drop the column `tailoredResumeUrl` on the `Resume` table. All the data in the column will be lost.
  - Added the required column `tailoreResumeUrlDocx` to the `Resume` table without a default value. This is not possible if the table is not empty.
  - Added the required column `tailoredResumeUrlPdf` to the `Resume` table without a default value. This is not possible if the table is not empty.
  - Made the column `atsScore` on table `Resume` required. This step will fail if there are existing NULL values in that column.

*/
-- AlterTable
ALTER TABLE "Resume" DROP COLUMN "generatedDocxUrl",
DROP COLUMN "tailoredResumeUrl",
ADD COLUMN     "tailoreResumeUrlDocx" TEXT NOT NULL,
ADD COLUMN     "tailoredResumeUrlPdf" TEXT NOT NULL,
ALTER COLUMN "atsScore" SET NOT NULL;
