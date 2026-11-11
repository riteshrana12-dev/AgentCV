"use client";

import { useRef, useCallback, useEffect } from "react";

import { EventHandler, InterviewEvent } from "@/types/interview";

import { AudioPlayerService } from "@/services/audioPlayer.service";

import { AudioCaptureService } from "@/services/audioCapture.service";

import { WebRTCSessionService } from "@/services/webrtcSession.service";

const FRAME_TYPE_AUDIO_OUT = 0x02;

export function useInterviewAudio(onEvent: EventHandler) {
  const socketRef = useRef(new WebRTCSessionService());

  const playerRef = useRef(new AudioPlayerService());

  const captureRef = useRef(new AudioCaptureService());

  const onEventRef = useRef(onEvent);
  const audioReceivedRef = useRef(false);
  const acceptAgentAudioRef = useRef(false);
  const sessionActiveRef = useRef(false);
  const fallbackDoneRef = useRef<Promise<void>>(Promise.resolve());
  const finishFallbackRef = useRef<(resumeMic: boolean) => void>(() => undefined);
  const fallbackResolveRef = useRef<() => void>(() => undefined);
  const micEnabledRef = useRef(false);
  const candidateListeningRef = useRef(false);
  const captureActiveRef = useRef(false);
  const agentSpeakingRef = useRef(false);

  const startMicCapture = useCallback(async () => {
    if (!micEnabledRef.current) {
      return;
    }

    if (captureActiveRef.current) {
      return;
    }

    if (!candidateListeningRef.current) {
      return;
    }

    captureActiveRef.current = true;

    try {
      await captureRef.current.start((pcmBytes) => {
        if (!micEnabledRef.current || !candidateListeningRef.current || agentSpeakingRef.current) {
          return;
        }

        socketRef.current.sendAudio(pcmBytes);
        onEventRef.current({
          type: "audio_chunk_sent",
          bytes: pcmBytes.byteLength,
        });
      });
    } catch (error) {
      captureActiveRef.current = false;
      throw error;
    }
  }, []);

  const stopMicCapture = useCallback(async () => {
    if (!captureActiveRef.current) {
      return;
    }

    captureActiveRef.current = false;
    await captureRef.current.stop();
  }, []);

  const resumeListeningAfterPlayback = useCallback(async () => {
    micEnabledRef.current = true;
    await playerRef.current.waitForPlaybackEnd();
    await fallbackDoneRef.current;
    agentSpeakingRef.current = false;
    candidateListeningRef.current = true;
    await startMicCapture();
  }, [startMicCapture]);

  const speakTextFallback = useCallback((text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      return;
    }

    if (!text?.trim() || !sessionActiveRef.current) {
      return;
    }

    agentSpeakingRef.current = true;
    candidateListeningRef.current = false;
    window.speechSynthesis.cancel();
    let finished = false;
    const finish = (resumeMic: boolean) => {
      if (finished) return;
      finished = true;
      fallbackResolveRef.current();
      fallbackResolveRef.current = () => undefined;
      if (resumeMic && sessionActiveRef.current) {
        agentSpeakingRef.current = false;
        micEnabledRef.current = true;
        candidateListeningRef.current = true;
        void startMicCapture();
      }
    };
    finishFallbackRef.current = (resumeMic) => finish(resumeMic);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.onend = () => finish(true);
    utterance.onerror = () => finish(true);
    window.speechSynthesis.speak(utterance);
  }, [startMicCapture]);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const handleTransportEvent = useCallback((event: InterviewEvent) => {
    if (event.type === "transport_error") {
      sessionActiveRef.current = false;
      micEnabledRef.current = false;
      finishFallbackRef.current(false);
      playerRef.current.stopPlayback();
      void stopMicCapture();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    }
    onEventRef.current(event);
  }, [stopMicCapture]);

  const handleServerMessage = useCallback(async (event: MessageEvent) => {
    if (typeof event.data === "string") {
      try {
        const parsed = JSON.parse(event.data) as InterviewEvent;

        if (parsed.type === "state_change") {
          if (parsed.state === "listening") {
            await resumeListeningAfterPlayback();
          }

          if (parsed.state === "thinking") {
            agentSpeakingRef.current = false;
            candidateListeningRef.current = false;
            await stopMicCapture();
          }

          if (parsed.state === "speaking") {
            candidateListeningRef.current = false;
            agentSpeakingRef.current = true;
            await stopMicCapture();
          }

          if (parsed.state === "ended") {
            agentSpeakingRef.current = false;
            candidateListeningRef.current = false;
          }
        }

        if (parsed.type === "ended") {
          sessionActiveRef.current = false;
          micEnabledRef.current = false;
          candidateListeningRef.current = false;
          agentSpeakingRef.current = false;
          finishFallbackRef.current(false);
          await stopMicCapture();
          playerRef.current.stopPlayback();
          socketRef.current.disconnect();
        }

        if (parsed.type === "agent_text") {
          audioReceivedRef.current = false;
          acceptAgentAudioRef.current = true;
          agentSpeakingRef.current = true;
          candidateListeningRef.current = false;
          finishFallbackRef.current(false);
          fallbackDoneRef.current = new Promise((resolve) => {
            fallbackResolveRef.current = resolve;
          });
          finishFallbackRef.current = () => fallbackResolveRef.current();
        }

        if (parsed.type === "agent_audio_fallback") {
          if (typeof window !== "undefined" && "speechSynthesis" in window) {
            speakTextFallback(parsed.text);
          } else {
            finishFallbackRef.current(false);
          }
        }

        onEventRef.current(parsed);
    } catch (error) {
      if (!(error instanceof SyntaxError)) {
        onEventRef.current({
          type: "error",
          detail: error instanceof Error ? error.message : "Interview audio handling failed.",
        });
      }
      }
      return;
    }

    const buf = new Uint8Array(event.data);
    const frameType = buf[0];
    const payload = buf.slice(1);

    if (frameType === FRAME_TYPE_AUDIO_OUT) {
      if (!acceptAgentAudioRef.current) return;
      acceptAgentAudioRef.current = false;
      audioReceivedRef.current = true;
      agentSpeakingRef.current = true;
      window.speechSynthesis?.cancel();
      finishFallbackRef.current(false);
      await playerRef.current.playChunk(payload);
    }
  }, [
    resumeListeningAfterPlayback,
    speakTextFallback,
    startMicCapture,
    stopMicCapture,
  ]);

  const connect = useCallback(
    async (apiBaseUrl: string, sessionId: string) => {
      sessionActiveRef.current = true;
      candidateListeningRef.current = false;
      try {
        await socketRef.current.connect(
          apiBaseUrl,
          sessionId,
          handleServerMessage,
          handleTransportEvent,
        );
      } catch (error) {
        sessionActiveRef.current = false;
        throw error;
      }
    },
    [handleServerMessage, handleTransportEvent],
  );

  const startCapture = useCallback(async () => {
    sessionActiveRef.current = true;
    micEnabledRef.current = true;
    if (candidateListeningRef.current && !captureActiveRef.current) {
      await startMicCapture();
    }
  }, [startMicCapture]);

  const stopCapture = useCallback(async () => {
    sessionActiveRef.current = false;
    micEnabledRef.current = false;
    candidateListeningRef.current = false;
    finishFallbackRef.current(false);
    playerRef.current.stopPlayback();
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    await stopMicCapture();
    await socketRef.current.stopAndWait();
  }, [stopMicCapture]);

  const disconnect = useCallback(async () => {
    sessionActiveRef.current = false;
    micEnabledRef.current = false;
    candidateListeningRef.current = false;
    agentSpeakingRef.current = false;
    await stopMicCapture();

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    finishFallbackRef.current(false);

    await playerRef.current.destroy();

    socketRef.current.disconnect();
  }, [stopMicCapture]);

  useEffect(() => {
    return () => {
      void disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    startCapture,
    stopCapture,
    disconnect,
  };
}
