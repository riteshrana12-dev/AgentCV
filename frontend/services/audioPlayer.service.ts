export class AudioPlayerService {
  private context: AudioContext | null = null;

  private nextPlaybackTime = 0;
  private activeSources = new Set<AudioBufferSourceNode>();
  private pendingChunks = 0;
  private playbackGeneration = 0;
  private playbackWaiters = new Set<() => void>();

  isPlaying(): boolean {
    return this.pendingChunks > 0 || this.activeSources.size > 0;
  }

  async playChunk(mp3Bytes: Uint8Array): Promise<void> {
    if (!this.context) {
      this.context = new AudioContext();
      this.nextPlaybackTime = this.context.currentTime;
    }

    const ctx = this.context;

    const arrayBuffer = mp3Bytes.buffer.slice(
      mp3Bytes.byteOffset,
      mp3Bytes.byteOffset + mp3Bytes.byteLength,
    ) as ArrayBuffer;

    const generation = this.playbackGeneration;
    this.pendingChunks++;
    let audioBuffer: AudioBuffer;
    try {
      audioBuffer = await ctx.decodeAudioData(arrayBuffer);
    } catch (error) {
      this.pendingChunks--;
      this.resolvePlaybackWaitersIfIdle();
      throw error;
    }
    if (generation !== this.playbackGeneration) {
      this.pendingChunks--;
      this.resolvePlaybackWaitersIfIdle();
      return;
    }

    const source = ctx.createBufferSource();
    this.activeSources.add(source);
    this.pendingChunks--;
    source.onended = () => {
      this.activeSources.delete(source);
      this.resolvePlaybackWaitersIfIdle();
    };

    source.buffer = audioBuffer;
    source.connect(ctx.destination);

    const startAt = Math.max(this.nextPlaybackTime, ctx.currentTime);

    source.start(startAt);

    this.nextPlaybackTime = startAt + audioBuffer.duration;
  }

  stopPlayback() {
    this.playbackGeneration++;
    for (const source of this.activeSources) {
      try {
        source.stop();
      } catch {
        // The source may finish between iteration and stop.
      }
    }
    this.activeSources.clear();
    this.nextPlaybackTime = this.context?.currentTime ?? 0;
    this.resolvePlaybackWaitersIfIdle();
  }

  waitForPlaybackEnd(): Promise<void> {
    if (!this.isPlaying()) return Promise.resolve();
    return new Promise((resolve) => this.playbackWaiters.add(resolve));
  }

  private resolvePlaybackWaitersIfIdle() {
    if (this.isPlaying()) return;
    for (const resolve of this.playbackWaiters) resolve();
    this.playbackWaiters.clear();
  }

  async destroy() {
    this.stopPlayback();
    if (this.context) {
      await this.context.close();
      this.context = null;
    }
    this.nextPlaybackTime = 0;
  }
}
