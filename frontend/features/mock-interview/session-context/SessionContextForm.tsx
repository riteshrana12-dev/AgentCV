"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/config/api";
import { positionsList } from "./constants";

export default function SessionContextForm() {
  const [companyName, setCompanyName] = useState("");
  const [resume, setResume] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [position, setPosition] = useState("");
  const [interviewType, setInterviewType] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [focusAreas, setFocusAreas] = useState("");
  const [duration, setDuration] = useState("");

  const router = useRouter();

  async function handleSubmit(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();

    if (
      !resume ||
      !companyName.trim() ||
      !position ||
      !interviewType ||
      !difficulty ||
      !duration ||
      !jd.trim()
    ) {
      alert(
        "Please complete all required fields before starting the mock interview.",
      );
      return;
    }

    const formData = new FormData();
    formData.append("companyName", companyName.trim());
    formData.append("resume", resume);
    formData.append("jd", jd.trim());
    formData.append("position", position);
    formData.append("interviewType", interviewType);
    formData.append("difficulty", difficulty);
    formData.append("duration", duration);
    formData.append("focusAreas", focusAreas.trim());

    try {
      const response = await api.post("/interview/mock-interview", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const sessionId = response.data?.sessionId;
      if (!sessionId) {
        throw new Error("Session ID not returned by the backend.");
      }

      router.push(`/mock-interview/interview/${sessionId}`);
    } catch (error: any) {
      console.error("Session creation failed:", error);
      alert(
        error?.response?.data?.message ||
          error?.response?.data?.error ||
          "Unable to create this mock interview session.",
      );
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="space-y-2">
        <label className="block font-medium">Company name</label>
        <input
          type="text"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          className="w-full rounded border border-slate-300 p-2"
          placeholder="e.g. Google"
        />
      </div>

      <div className="space-y-2">
        <label className="block font-medium">Resume file</label>
        <input
          type="file"
          accept=".pdf,.doc,.docx"
          onChange={(e) => setResume(e.target.files?.[0] || null)}
          className="w-full rounded border border-slate-300 p-2"
        />
      </div>

      <div className="space-y-2">
        <label className="block font-medium">Job description</label>
        <textarea
          value={jd}
          onChange={(e) => setJd(e.target.value)}
          className="h-32 w-full rounded border border-slate-300 p-2"
          placeholder="Paste the job description here..."
        />
      </div>

      <div className="space-y-2">
        <label className="block font-medium">Position</label>
        <div className="grid gap-2 max-h-64 overflow-y-auto rounded border border-slate-200 p-3">
          {positionsList.map((pos) => (
            <label key={pos} className="flex items-center gap-2">
              <input
                type="radio"
                name="position"
                value={pos}
                checked={position === pos}
                onChange={(e) => setPosition(e.target.value)}
              />
              <span>{pos}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <label className="block font-medium">Interview type</label>
        <div className="space-y-2">
          {[
            ["technical", "Technical"],
            ["behavioral", "Behavioral"],
            ["mixed", "Mixed"],
          ].map(([value, label]) => (
            <label key={value} className="flex items-center gap-2">
              <input
                type="radio"
                name="interview_type"
                value={value}
                checked={interviewType === value}
                onChange={(e) => setInterviewType(e.target.value)}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <label className="block font-medium">Difficulty</label>
        <div className="space-y-2">
          {[
            ["junior", "Junior"],
            ["mid", "Mid"],
            ["senior", "Senior"],
          ].map(([value, label]) => (
            <label key={value} className="flex items-center gap-2">
              <input
                type="radio"
                name="difficulty"
                value={value}
                checked={difficulty === value}
                onChange={(e) => setDifficulty(e.target.value)}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <label className="block font-medium">Focus areas</label>
        <input
          type="text"
          value={focusAreas}
          onChange={(e) => setFocusAreas(e.target.value)}
          className="w-full rounded border border-slate-300 p-2"
          placeholder="e.g. React, system design, backend architecture"
        />
      </div>

      <div className="space-y-2">
        <label className="block font-medium">Duration (minutes)</label>
        <input
          type="number"
          min={10}
          max={60}
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
          className="w-full rounded border border-slate-300 p-2"
          placeholder="e.g. 25"
        />
      </div>

      <button
        type="submit"
        className="w-full rounded bg-green-600 px-4 py-2 font-medium text-white hover:bg-green-700"
      >
        Start interview session
      </button>
    </form>
  );
}
