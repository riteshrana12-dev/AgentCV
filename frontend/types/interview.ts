export type InterviewEvent =
  | {
      type: "state_change";
      state: "preparing" | "listening" | "thinking" | "speaking" | "ended";
    }
  | {
      type: "transcript";
      text: string;
      is_final: boolean;
    }
  | {
      type: "agent_text";
      text: string;
    }
  | {
      type: "agent_audio_fallback";
      text: string;
    }
  | {
      type: "error";
      detail: string;
    }
  | {
      type: "transport_error";
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
