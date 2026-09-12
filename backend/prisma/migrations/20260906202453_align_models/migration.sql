/*
  Warnings:

  - You are about to drop the column `newResumePath` on the `Resume` table. All the data in the column will be lost.
  - You are about to drop the column `parseResume` on the `Resume` table. All the data in the column will be lost.
  - You are about to drop the column `uploadedResumePath` on the `Resume` table. All the data in the column will be lost.
  - You are about to drop the column `password` on the `User` table. All the data in the column will be lost.
  - Added the required column `fileName` to the `Resume` table without a default value. This is not possible if the table is not empty.
  - Added the required column `fileSize` to the `Resume` table without a default value. This is not possible if the table is not empty.
  - Added the required column `fileType` to the `Resume` table without a default value. This is not possible if the table is not empty.
  - Added the required column `jd` to the `Resume` table without a default value. This is not possible if the table is not empty.
  - Added the required column `originalResumePath` to the `Resume` table without a default value. This is not possible if the table is not empty.
  - Added the required column `originalResumeUrl` to the `Resume` table without a default value. This is not possible if the table is not empty.
  - Added the required column `updatedAt` to the `Resume` table without a default value. This is not possible if the table is not empty.
  - Added the required column `hashedPassword` to the `User` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "Resume" DROP CONSTRAINT "Resume_userId_fkey";

-- AlterTable
ALTER TABLE "Resume" DROP COLUMN "newResumePath",
DROP COLUMN "parseResume",
DROP COLUMN "uploadedResumePath",
ADD COLUMN     "atsScore" INTEGER,
ADD COLUMN     "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN     "fileName" TEXT NOT NULL,
ADD COLUMN     "fileSize" INTEGER NOT NULL,
ADD COLUMN     "fileType" TEXT NOT NULL,
ADD COLUMN     "generatedDocxUrl" TEXT,
ADD COLUMN     "jd" TEXT NOT NULL,
ADD COLUMN     "originalResumePath" TEXT NOT NULL,
ADD COLUMN     "originalResumeUrl" TEXT NOT NULL,
ADD COLUMN     "tailoredResumeUrl" TEXT,
ADD COLUMN     "updatedAt" TIMESTAMP(3) NOT NULL;

-- AlterTable
ALTER TABLE "User" DROP COLUMN "password",
ADD COLUMN     "hashedPassword" TEXT NOT NULL;

-- AddForeignKey
ALTER TABLE "Resume" ADD CONSTRAINT "Resume_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
