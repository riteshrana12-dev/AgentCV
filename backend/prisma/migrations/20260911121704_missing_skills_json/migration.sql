/*
  Warnings:

  - Changed the type of `missingSkills` on the `Suggestion` table. No cast exists, the column would be dropped and recreated, which cannot be done if there is data, since the column is required.

*/
-- AlterTable
ALTER TABLE "Suggestion" DROP COLUMN "missingSkills",
ADD COLUMN     "missingSkills" JSONB NOT NULL;
