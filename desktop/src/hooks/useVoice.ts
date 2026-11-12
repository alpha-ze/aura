import { useCallback, useRef } from "react";
import { useVoiceStore } from "@/store";
import { useChat } from "./useChat";

/**
 * Voice input hook.
 * In Phase 1 this provides the UI wiring for voice state.
 * Full STT/VAD is implemented in Phase 4.
 * 
 * Architecture:
 *  - toggleVoice() starts/stops listening
 *  - When recording stops, audio is POSTed to /api/voice on the backend
 *  - Backend returns transcript → feeds into the agent as a text message
 */
export function useVoice() {
  const { voiceState, setVoiceState, setTranscript, setAudioLevel } = useVoiceStore();
  const { sendMessage } = useChat();
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);

  const stopAudioLevelTracking = () => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    setAudioLevel(0);
  };

  const trackAudioLevel = (stream: MediaStream) => {
    audioContextRef.current = new AudioContext();
    analyserRef.current = audioContextRef.current.createAnalyser();
    analyserRef.current.fftSize = 256;
    const source = audioContextRef.current.createMediaStreamSource(stream);
    source.connect(analyserRef.current);
    const data = new Uint8Array(analyserRef.current.frequencyBinCount);

    const tick = () => {
      if (!analyserRef.current) return;
      analyserRef.current.getByteFrequencyData(data);
      const avg = data.reduce((a, b) => a + b, 0) / data.length;
      setAudioLevel(Math.min(avg / 128, 1));
      animFrameRef.current = requestAnimationFrame(tick);
    };
    tick();
  };

  const startListening = useCallback(async () => {
    if (voiceState === "listening") return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setVoiceState("listening");
      setTranscript("");
      chunksRef.current = [];
      trackAudioLevel(stream);

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stopAudioLevelTracking();
        stream.getTracks().forEach((t) => t.stop());
        audioContextRef.current?.close();

        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        setVoiceState("processing");

        try {
          const formData = new FormData();
          formData.append("audio", audioBlob, "voice.webm");

          const response = await fetch("http://127.0.0.1:8765/api/voice", {
            method: "POST",
            body: formData,
          });

          if (response.status === 503) {
            // Voice not installed — show helpful message in chat
            setVoiceState("idle");
            await sendMessage(
              "I tried to use voice input but faster-whisper is not installed. " +
              "You can install it by running: pip install faster-whisper in the backend folder. " +
              "For now, please type your message."
            );
            return;
          }

          if (response.ok) {
            const data = await response.json() as { transcript: string };
            if (data.transcript?.trim()) {
              setTranscript(data.transcript);
              setVoiceState("idle");
              await sendMessage(data.transcript);
            } else {
              setVoiceState("idle");
            }
          } else {
            setVoiceState("idle");
          }
        } catch {
          setVoiceState("idle");
        }
      };

      recorder.start(100); // Collect data in 100ms chunks
    } catch {
      setVoiceState("error");
      setTimeout(() => setVoiceState("idle"), 2000);
    }
  }, [voiceState, setVoiceState, setTranscript, sendMessage]);

  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    stopAudioLevelTracking();
  }, []);

  const toggleVoice = useCallback(() => {
    if (voiceState === "listening") {
      stopListening();
    } else if (voiceState === "idle") {
      startListening();
    }
  }, [voiceState, startListening, stopListening]);

  return { voiceState, toggleVoice, startListening, stopListening };
}
