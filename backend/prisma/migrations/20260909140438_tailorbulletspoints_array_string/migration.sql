/*
  Warnings:

  - The `tailoredBulletsPoints` column on the `Suggestion` table would be dropped and recreated. This will lead to data loss if there is data in the column.

*/
-- AlterTable
ALTER TABLE "Suggestion" DROP COLUMN "tailoredBulletsPoints",
ADD COLUMN     "tailoredBulletsPoints" TEXT[];
