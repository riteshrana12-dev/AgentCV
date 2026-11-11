import type { EventHandler } from "@/types/interview";

export type WebRTCSignalType = "offer" | "answer" | "candidate";

export type WebRTCSignalPayload = {
  sessionId: string;
  peerId: string;
  type: WebRTCSignalType;
  payload?: Record<string, unknown> | null;
};

export class WebRTCSessionService {
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private pollingHandle: number | null = null;
  private apiBaseUrl = "http://localhost:3001/api/v1";
  private sessionId = "";
  private peerId = "";
  private messageHandler: ((event: MessageEvent) => void) | null = null;
  private eventHandler: EventHandler | null = null;
  private pendingRemoteCandidates: RTCIceCandidateInit[] = [];
  private stopResolver: (() => void) | null = null;
  private stopRejecter: ((error: Error) => void) | null = null;
  private stopping = false;

  async connect(
    apiBaseUrl: string,
    sessionId: string,
    onMessage: (event: MessageEvent) => void,
    onEvent: EventHandler,
  ) {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("This browser does not support microphone capture.");
    }
    if (!("RTCPeerConnection" in window)) {
      throw new Error("WebRTC is not supported in this browser.");
    }

    this.apiBaseUrl = apiBaseUrl.replace(/\/$/, "");
    this.sessionId = sessionId;
    this.peerId = crypto.randomUUID();
    this.messageHandler = onMessage;
    this.eventHandler = onEvent;
    this.pendingRemoteCandidates = [];
    this.stopping = false;

    const peerConnection = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });
    this.peerConnection = peerConnection;

    const dataChannel = peerConnection.createDataChannel("interview", {
      ordered: true,
    });
    this.dataChannel = dataChannel;

    let resolveOpen!: () => void;
    let rejectOpen!: (error: Error) => void;
    const channelOpened = new Promise<void>((resolve, reject) => {
      resolveOpen = resolve;
      rejectOpen = reject;
    });

    dataChannel.onopen = () => {
      resolveOpen();
    };

    dataChannel.onmessage = (event) => {
      if (typeof event.data === "string") {
        try {
          const parsed = JSON.parse(event.data) as { type?: string };
          if (parsed.type === "ended") {
            this.resolveStopWait();
          }
        } catch {
          // The interview hook will report or ignore malformed event messages.
        }
      }
      this.messageHandler?.(event);
    };

    dataChannel.onerror = () => {
      this.failTransport("WebRTC data channel error.");
    };

    dataChannel.onclose = () => {
      this.rejectStopWait(new Error("WebRTC data channel closed before the interview ended."));
      if (!this.stopping) this.failTransport("WebRTC data channel closed unexpectedly.");
    };

    peerConnection.onicecandidate = (event) => {
      if (!event.candidate) return;
      void this.sendSignal({
        sessionId: this.sessionId,
        peerId: this.peerId,
        type: "candidate",
        payload: { candidate: event.candidate.toJSON() },
      }).catch((error) => this.reportError(error));
    };

    peerConnection.onconnectionstatechange = () => {
      if (peerConnection.connectionState === "failed") {
        const detail = "WebRTC connection failed. Please retry the interview.";
        this.failTransport(detail);
        rejectOpen(new Error(detail));
      }
    };

    const timeout = window.setTimeout(() => {
      rejectOpen(new Error("Timed out waiting for the WebRTC data channel."));
    }, 20_000);

    try {
      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);
      await this.sendSignal({
        sessionId: this.sessionId,
        peerId: this.peerId,
        type: "offer",
        payload: { sdp: offer.sdp, type: offer.type },
      });
      this.startPollingForSignals();
      await channelOpened;
    } catch (error) {
      await this.stop();
      throw error;
    } finally {
      window.clearTimeout(timeout);
    }
  }

  sendAudio(pcmBytes: Uint8Array) {
    if (!this.dataChannel || this.dataChannel.readyState !== "open") return;

    const frame = new Uint8Array(1 + pcmBytes.byteLength);
    frame[0] = 0x01;
    frame.set(pcmBytes, 1);
    this.dataChannel.send(frame.buffer);
  }

  async stopAndWait() {
    if (!this.dataChannel || this.dataChannel.readyState !== "open") return;

    const ended = new Promise<void>((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        this.stopResolver = null;
        this.stopRejecter = null;
        reject(new Error("Timed out waiting for the AI engine to finish the interview."));
      }, 20_000);

      this.stopResolver = () => {
        window.clearTimeout(timeout);
        this.stopResolver = null;
        this.stopRejecter = null;
        resolve();
      };
      this.stopRejecter = (error) => {
        window.clearTimeout(timeout);
        this.stopResolver = null;
        this.stopRejecter = null;
        reject(error);
      };
    });

    this.dataChannel.send(JSON.stringify({ type: "stop" }));
    await ended;
  }

  isConnected(): boolean {
    return this.dataChannel?.readyState === "open";
  }

  async stop() {
    this.stopping = true;
    if (this.sessionId && this.peerId) {
      void fetch(`${this.apiBaseUrl}/interview/webrtc/close`, {
        method: "POST",
        credentials: "include",
        keepalive: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: this.sessionId, peerId: this.peerId }),
      }).catch(() => undefined);
    }

    if (this.pollingHandle !== null) {
      window.clearInterval(this.pollingHandle);
      this.pollingHandle = null;
    }

    this.rejectStopWait(new Error("Interview connection closed."));
    this.dataChannel?.close();
    this.peerConnection?.close();
    this.dataChannel = null;
    this.peerConnection = null;
    this.pendingRemoteCandidates = [];
  }

  disconnect() {
    void this.stop();
  }

  private async sendSignal(signal: WebRTCSignalPayload) {
    const response = await fetch(`${this.apiBaseUrl}/interview/webrtc/signal`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(signal),
    });

    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as { message?: string };
      throw new Error(body.message ?? "Failed to send WebRTC signal.");
    }
  }

  private startPollingForSignals() {
    let pollInFlight = false;
    let consecutiveFailures = 0;

    const poll = async () => {
      if (pollInFlight || !this.peerConnection) return;
      pollInFlight = true;

      try {
        const response = await fetch(
          `${this.apiBaseUrl}/interview/webrtc/signal?sessionId=${encodeURIComponent(this.sessionId)}&peerId=${encodeURIComponent(this.peerId)}`,
          { credentials: "include" },
        );
        if (!response.ok) throw new Error("Failed to retrieve WebRTC signals.");
        consecutiveFailures = 0;

        const data = (await response.json()) as {
          signals?: Array<{
            peerId: string;
            type: WebRTCSignalType;
            payload?: Record<string, unknown> | null;
          }>;
        };

        const signals = data.signals ?? [];
        const answer = signals.find((signal) => signal.type === "answer");
        if (answer?.payload?.sdp && this.peerConnection.signalingState !== "stable") {
          await this.peerConnection.setRemoteDescription({
            type: "answer",
            sdp: String(answer.payload.sdp),
          });
          this.eventHandler?.({ type: "state_change", state: "listening" });

          for (const candidate of this.pendingRemoteCandidates.splice(0)) {
            await this.addRemoteCandidate(candidate);
          }
        }

        for (const signal of signals) {
          if (signal.type !== "candidate" || !signal.payload?.candidate) continue;
          const candidate = signal.payload.candidate as RTCIceCandidateInit;
          if (this.peerConnection.remoteDescription) {
            await this.addRemoteCandidate(candidate);
          } else {
            this.pendingRemoteCandidates.push(candidate);
          }
        }
      } catch (error) {
        consecutiveFailures++;
        if (consecutiveFailures >= 5) {
          this.failTransport(
            error instanceof Error
              ? error.message
              : "WebRTC signaling stopped responding.",
          );
        } else {
          this.reportError(error);
        }
      } finally {
        pollInFlight = false;
      }
    };

    void poll();
    this.pollingHandle = window.setInterval(() => void poll(), 500);
  }

  private async addRemoteCandidate(candidate: RTCIceCandidateInit) {
    try {
      await this.peerConnection?.addIceCandidate(new RTCIceCandidate(candidate));
    } catch (error) {
      this.reportError(error);
    }
  }

  private resolveStopWait() {
    this.stopResolver?.();
  }

  private rejectStopWait(error: Error) {
    this.stopRejecter?.(error);
  }

  private reportError(error: unknown) {
    this.eventHandler?.({
      type: "error",
      detail: error instanceof Error ? error.message : "WebRTC signaling failed.",
    });
  }

  private failTransport(detail: string) {
    this.eventHandler?.({ type: "transport_error", detail });
    void this.stop();
  }
}
