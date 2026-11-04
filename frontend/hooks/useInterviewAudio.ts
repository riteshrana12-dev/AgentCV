"use client";

import { useRef, useCallback, useEffect } from "react";
import { EventHandler } from "@/types/interview";
import { AudioPlayerService } from "@/services/audioPlayer.service";
import { AudioCaptureService } from "@/services/audioCapture.service";
import { InterviewSocketService } from "@/services/interviewSocket.service";

export function useInterviewAudio(onEvent: EventHandler) {
  const playerRef = useRef(new AudioPlayerService());
  const captureRef = useRef(new AudioCaptureService());
  const socketRef = useRef(new InterviewSocketService());
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const connect = useCallback(async (nodeWsUrl: string, sessionId: string) => {
    await socketRef.current.connect(
      nodeWsUrl,
      sessionId,
      () => {},
      onEventRef.current,
    );
  }, []);

  const disconnect = useCallback(() => {
    socketRef.current.disconnect();
  }, []);

  const startCapture = useCallback(async () => {
    await captureRef.current.start((pcmBytes) => {
      socketRef.current.sendAudio(pcmBytes);
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
