import { downsampleBuffer, float32ToInt16 } from "@/utils/audio.utils";

const TARGET_SAMPLE_RATE = 16000;

export class AudioCaptureService {
  private audioContext: AudioContext | null = null;

  private micStream: MediaStream | null = null;

  private workletNode: AudioWorkletNode | null = null;

  async start(onAudioFrame: (pcmBytes: Uint8Array) => void) {
    const micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    this.micStream = micStream;

    const audioContext = new AudioContext({
      sampleRate: TARGET_SAMPLE_RATE,
    });

    this.audioContext = audioContext;
    await audioContext.resume();

    await audioContext.audioWorklet.addModule("/worklet-processor.js");

    const source = audioContext.createMediaStreamSource(micStream);

    const workletNode = new AudioWorkletNode(
      audioContext,
      "pcm-worklet-processor",
    );

    this.workletNode = workletNode;

    const actualRate = audioContext.sampleRate;

    workletNode.port.onmessage = (event: MessageEvent<Float32Array>) => {
      const float32 = event.data;

      const resampled =
        actualRate === TARGET_SAMPLE_RATE
          ? float32
          : downsampleBuffer(float32, actualRate, TARGET_SAMPLE_RATE);

      const pcm16 = float32ToInt16(resampled);
      const pcmBytes = new Uint8Array(pcm16.length * 2);
      const view = new DataView(pcmBytes.buffer);

      for (let i = 0; i < pcm16.length; i++) {
        view.setInt16(i * 2, pcm16[i], true);
      }

      onAudioFrame(pcmBytes);
    };

    source.connect(workletNode);
    // Keep the worklet in the active audio graph. It outputs silence, so this
    // does not play microphone audio back through the speakers.
    workletNode.connect(audioContext.destination);
  }

  async stop() {
    this.workletNode?.disconnect();

    this.micStream?.getTracks().forEach((t) => t.stop());

    await this.audioContext?.close();

    this.workletNode = null;
    this.audioContext = null;
    this.micStream = null;
  }
}
