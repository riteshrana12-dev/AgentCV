class PCMWorkletProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.pending = [];
    // Silero VAD on the AI side consumes 512 samples (32 ms) per frame.
    // Send silence too: without it the server cannot detect end of turn.
    this.bufferSize = 512;
  }

  process(inputs, outputs) {
    const channel = inputs[0]?.[0];

    if (!channel) {
      return true;
    }

    this.pending.push(channel.slice());
    if (this.pending.reduce((sum, block) => sum + block.length, 0) >= this.bufferSize) {
      const chunk = this.merge(this.pending);
      const frame = chunk.slice(0, this.bufferSize);
      this.port.postMessage(frame, [frame.buffer]);
      const remainder = chunk.slice(this.bufferSize);
      this.pending = [];
      if (remainder.length > 0) this.pending.push(remainder);
    }

    for (const channelOut of outputs[0] ?? []) {
      channelOut.fill(0);
    }

    return true;
  }

  merge(blocks) {
    const totalLength = blocks.reduce((sum, block) => sum + block.length, 0);
    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const block of blocks) {
      merged.set(block, offset);
      offset += block.length;
    }
    return merged;
  }
}

registerProcessor("pcm-worklet-processor", PCMWorkletProcessor);
