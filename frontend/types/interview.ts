export type InterviewEvent =
  | {
      type: "state_change";
      state: "listening" | "thinking" | "speaking" | "ended";
    }
  | {
      type: "transcript";
      text: string;
    }
  | {
      type: "agent_text";
      text: string;
    }
  | {
      type: "error";
      detail: string;
    }
  | {
      type: "audio_chunk_received";
      bytes: number;
    }
  | {
      type: "audio_chunk_sent";
      bytes: number;
    }
  | {
      type: "ended";
    };

export type EventHandler = (event: InterviewEvent) => void;
