class PCMWorkletProcessor extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const input = inputs[0]; // audio from the mic
    if (input && input[0]) {
      this.port.postMessage(input[0].slice()); // send a copy to the main code
    }
    for (const channel of outputs[0] ?? []) {
      channel.fill(0); // keep the graph active without monitoring the microphone
    }
    return true; // keep running
  }
}
registerProcessor("pcm-worklet-processor", PCMWorkletProcessor);
