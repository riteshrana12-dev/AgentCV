"use client";

import { useRef, useCallback, useEffect } from "react";
import { EventHandler } from "@/types/interview";
import { InterviewSocketService } from "@/services/interviewSocket.service";

export function useInterviewAudio(onEvent: EventHandler) {
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

  return {
    connect,
    disconnect,
  };
}
