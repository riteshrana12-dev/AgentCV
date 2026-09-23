"use client";
import { useState } from "react";
import api from "@/config/api";

export default function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmmit(e: React.FormEvent) {
    e.preventDefault();
    const formData = new FormData();

    if (email) formData.append("email", email);
    if (password) formData.append("password", password);

    const res = await api.post(
      "/auth/signin",
      { email, password },
      {
        headers: { "Content-Type": "application/json" },
      },
    );

    console.log(res.data);

    alert("signIn successfull");
  }

  return (
    <form action="" onSubmit={handleSubmmit}>
      <input
        type="text"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="text"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <button
        type="submit"
        className="bg-green-600 text-white px-4 py-2 rounded w-full"
      >
        Sign In
      </button>
    </form>
  );
}
