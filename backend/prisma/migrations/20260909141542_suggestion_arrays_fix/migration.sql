/*
  Warnings:

  - The `matchedSkills` column on the `Suggestion` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - The `missingSkills` column on the `Suggestion` table would be dropped and recreated. This will lead to data loss if there is data in the column.

*/
-- AlterTable
ALTER TABLE "Suggestion" DROP COLUMN "matchedSkills",
ADD COLUMN     "matchedSkills" TEXT[],
DROP COLUMN "missingSkills",
ADD COLUMN     "missingSkills" TEXT[];
