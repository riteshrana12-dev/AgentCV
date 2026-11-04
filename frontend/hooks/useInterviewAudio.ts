"use client";

import { useRef, useCallback, useEffect } from "react";
import { EventHandler } from "@/types/interview";
import { AudioPlayerService } from "@/services/audioPlayer.service";
import { AudioCaptureService } from "@/services/audioCapture.service";
import { InterviewSocketService } from "@/services/interviewSocket.service";
import { InterviewEvent } from "@/types/interview";

const FRAME_TYPE_AUDIO_OUT = 0x02;

export function useInterviewAudio(onEvent: EventHandler) {
  const playerRef = useRef(new AudioPlayerService());
  const captureRef = useRef(new AudioCaptureService());
  const socketRef = useRef(new InterviewSocketService());
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const handleServerMessage = useCallback(async (event: MessageEvent) => {
    if (typeof event.data === "string") {
      try {
        const parsed = JSON.parse(event.data) as InterviewEvent;
        onEventRef.current(parsed);
      } catch {
        // Ignore malformed messages
      }

      return;
    }

    const buf = new Uint8Array(event.data);
    const frameType = buf[0];
    const payload = buf.slice(1);

    if (frameType === FRAME_TYPE_AUDIO_OUT) {
      await playerRef.current.playChunk(payload);
    }
  }, []);

  const connect = useCallback(
    async (nodeWsUrl: string, sessionId: string) => {
      await socketRef.current.connect(
        nodeWsUrl,
        sessionId,
        handleServerMessage,
        onEventRef.current,
      );
    },
    [handleServerMessage],
  );

  const disconnect = useCallback(() => {
    socketRef.current.disconnect();
  }, []);

  const startCapture = useCallback(async () => {
    await captureRef.current.start((pcmBytes) => {
      socketRef.current.sendAudio(pcmBytes);
      onEventRef.current({
        type: "audio_chunk_sent",
        bytes: pcmBytes.byteLength,
      });
    });
  }, []);

  const stopCapture = useCallback(async () => {
    await captureRef.current.stop();
  }, []);

  return {
    connect,
    startCapture,
    stopCapture,
    disconnect,
  };
}
