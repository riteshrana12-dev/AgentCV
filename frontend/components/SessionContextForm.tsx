"use client";

import { useState } from "react";
import api from "@/config/api";
import { useRouter } from "next/navigation";

export default function SessionConextForm() {
  const [companyName, setCompanyName] = useState("");
  const [resume, setResume] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [position, setPosition] = useState("");
  const [interviewType, setInterviewType] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [focusAreas, setFocusAreas] = useState("");
  const [duration, setDuration] = useState("");

  const router = useRouter();

  // Unified list of positions for clean mapping and proper state checking
  const positionsList = [
    "Software Engineer",
    "Frontend Engineer",
    "Backend Engineer",
    "Full Stack Engineer",
    "MERN Developer",
    "React Developer",
    "Node Developer",
    "JavaScript Developer",
    "DevOps Engineer",
    "Cloud Architect",
    "Site Reliability Engineer",
    "Cybersecurity Engineer",
    "AI Engineer",
    "Machine Learning Engineer",
    "Data Scientist",
    "Data Engineer",
    "MLOps Engineer",
    "NLP Engineer",
    "Computer Vision Engineer",
    "Android Developer",
    "iOS Developer",
    "Mobile App Developer",
    "Embedded Systems Engineer",
    "Game Developer",
    "QA Automation Engineer",
    "Solutions Architect",
  ];

  async function handleSubmit(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();

    if (!resume || !companyName.trim() || !position || !interviewType || !difficulty || !duration || !jd.trim()) {
      alert("Please complete all required fields before starting the mock interview.");
      return;
    }

    const formData = new FormData();
    formData.append("companyName", companyName);
    formData.append("resume", resume);
    formData.append("jd", jd);
    formData.append("position", position);
    formData.append("interviewType", interviewType);
    formData.append("difficulty", difficulty);
    formData.append("duration", duration);
    formData.append("focusAreas", focusAreas);

    try {
      const response = await api.post("/interview/mock-interview/", formData);
      const sessionId = response.data.sessionId;
      router.push(`/mock-interview/interview/${sessionId}`);
    } catch (error: any) {
      console.error("Session creation failed:", error);
      alert(error?.response?.data?.message || "Unable to create this mock interview session.");
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>company name</label>
      <input
        type="text"
        name="company_name"
        value={companyName}
        onChange={(e) => setCompanyName(e.target.value)}
      />

      <label>file</label>
      <input
        type="file"
        name="resume"
        accept=".pdf,.doc,.docx"
        onChange={(e) => setResume(e.target.files?.[0] || null)}
      />

      <label>jd</label>
      <textarea
        placeholder="Paste Job Description here..."
        value={jd}
        onChange={(e) => setJd(e.target.value)}
        className="border p-2 w-full h-32"
      />

      <label>position</label>
      <div>
        {positionsList.map((pos) => (
          <label key={pos} style={{ display: "block" }}>
            <input
              type="radio"
              name="position"
              value={pos}
              checked={position === pos}
              onChange={(e) => setPosition(e.target.value)}
            />
            {pos === "Site Reliability Engineer"
              ? "Site Reliability Engineer (SRE)"
              : pos}
          </label>
        ))}
      </div>

      <input type="text" name="others" placeholder="Other position" />

      <label>interview type</label>
      <div>
        <label style={{ display: "block" }}>
          <input
            type="radio"
            name="interview_type"
            value="technical"
            checked={interviewType === "technical"}
            onChange={(e) => setInterviewType(e.target.value)}
          />
          Technical
        </label>
        <label style={{ display: "block" }}>
          <input
            type="radio"
            name="interview_type"
            value="behavioral"
            checked={interviewType === "behavioral"}
            onChange={(e) => setInterviewType(e.target.value)}
          />
          Behavioral
        </label>
        <label style={{ display: "block" }}>
          <input
            type="radio"
            name="interview_type"
            value="mixed"
            checked={interviewType === "mixed"}
            onChange={(e) => setInterviewType(e.target.value)}
          />
          Mixed
        </label>
      </div>

      <label>difficulty</label>
      <div>
        <label style={{ display: "block" }}>
          <input
            type="radio"
            name="difficulty"
            value="junior"
            checked={difficulty === "junior"}
            onChange={(e) => setDifficulty(e.target.value)}
          />
          Junior
        </label>
        <label style={{ display: "block" }}>
          <input
            type="radio"
            name="difficulty"
            value="mid"
            checked={difficulty === "mid"}
            onChange={(e) => setDifficulty(e.target.value)}
          />
          Mid
        </label>
        <label style={{ display: "block" }}>
          <input
            type="radio"
            name="difficulty"
            value="senior"
            checked={difficulty === "senior"}
            onChange={(e) => setDifficulty(e.target.value)}
          />
          Senior
        </label>
      </div>

      <label>focus area</label>
      <input
        type="text"
        name="focus_area"
        value={focusAreas}
        onChange={(e) => setFocusAreas(e.target.value)}
      />

      <label>duration</label>
      <input
        type="text"
        name="duration"
        value={duration}
        onChange={(e) => setDuration(e.target.value)}
      />

      <button
        type="submit"
        className="bg-green-600 text-white px-4 py-2 rounded w-full"
      >
        Submit the Session Context
      </button>
    </form>
  );
}
