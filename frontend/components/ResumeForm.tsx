"use client";
import { useState } from "react";
import api from "@/config/api";

export default function ResumeForm() {
  const [resume, setResume] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [githubId, setGithubId] = useState("");

  async function handleSubmit(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();

    const formData = new FormData();
    if (resume) formData.append("resume", resume);
    formData.append("jd", jd);
    formData.append("github_username", githubId);

    const res = await api.post("/upload/resume", formData);
    if (res.data.data.success) {
      console.log(
        "unidirection connection is started stream start from frontend side",
      );
      const resumeId = res.data.data.resumeId;

      const eventSource = new EventSource(
        `http://localhost:3001/api/v1/resume/stream-status/${resumeId}`,
        { withCredentials: true },
      );

      eventSource.onopen = () => {
        console.log("SSE CONNECTION OPENED");
      };

      eventSource.onmessage = (event) => {
        console.log("SSE MESSAGE RECEIVED:", event.data);
        const data = JSON.parse(event.data);

        if (data.status === "finished") {
          console.log("Resume completed:", data);
          eventSource.close();
        }
        console.log("update  ", data);
      };

      eventSource.onerror = (error) => {
        console.error("SSE ERROR:", error);
        console.log("ReadyState:", eventSource.readyState);
      };
    }
    alert("Resume submitted successfully!");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 w-full max-w-md bg-white p-6 rounded shadow"
    >
      <input
        type="file"
        accept=".pdf,.doc,.docx"
        onChange={(e) => setResume(e.target.files?.[0] || null)}
        className="border p-2 w-full"
      />

      <textarea
        placeholder="Paste Job Description here..."
        value={jd}
        onChange={(e) => setJd(e.target.value)}
        className="border p-2 w-full h-32"
      />

      <input
        type="text"
        placeholder="GitHub Username"
        value={githubId}
        onChange={(e) => setGithubId(e.target.value)}
        className="border p-2 w-full"
      />

      <button
        type="submit"
        className="bg-green-600 text-white px-4 py-2 rounded w-full"
      >
        Upload & Tailor Resume
      </button>
    </form>
  );
}
