import React, { useState, useRef } from "react";
import { Camera, ImageIcon } from "lucide-react";
import { Button } from "../reusable-ui-components/Button"
import { API_ENDPOINTS } from "../api/endpoints";

import ChatPanel from "./sub-views/ChatPanel";
import CameraPanel from "./sub-views/CameraPanel";
import ImageUploader from "./sub-views/ImageUploader";
import ControlsPanel from "./sub-views/ControlsPanel";
import Visualizer from "./sub-views/Visualizer";
import "./InferenceWindow.css";

export default function InferenceWindow() {
  const [image, setImage] = useState(null);
  const [text, setText] = useState("");
  const [listening, setListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [audioBlob, setAudioBlob] = useState(null);
  const [flashcard, setFlashcard] = useState(null);
  const [mode, setMode] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [showFlash, setShowFlash] = useState(false);
  const [volume, setVolume] = useState(0);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const sourceRef = useRef(null);
  const volumeIntervalRef = useRef(null);


  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(URL.createObjectURL(file));
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Camera access error", err);
    }
  };

  const captureImage = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL("image/png");
      setCapturedImage(dataUrl);
      setShowFlash(true);
      setTimeout(() => setShowFlash(false), 200);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        setTranscribing(true);
        stopVolumeMeter();
        await transcribeWithWhisper(blob);
        setTranscribing(false);
      };

      mediaRecorder.start();
      setupVolumeMeter(stream);
      setListening(true);
    } catch (err) {
      console.error("Microphone access error", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && listening) {
      mediaRecorderRef.current.stop();
      setListening(false);
    }
  };

  const setupVolumeMeter = (stream) => {
    audioContextRef.current = new AudioContext();
    analyserRef.current = audioContextRef.current.createAnalyser();
    sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
    sourceRef.current.connect(analyserRef.current);
    analyserRef.current.fftSize = 256;
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    volumeIntervalRef.current = setInterval(() => {
      analyserRef.current.getByteFrequencyData(dataArray);
      const avg = dataArray.reduce((a, b) => a + b, 0) / bufferLength;
      setVolume(avg);
    }, 100);
  };

  const stopVolumeMeter = () => {
    if (volumeIntervalRef.current) {
      clearInterval(volumeIntervalRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    setVolume(0);
  };

  const transcribeWithWhisper = async (blob) => {
    try {
      const formData = new FormData();
      formData.append("audio", blob, "recording.webm");

      const response = await fetch(API_ENDPOINTS.TRANSCRIBE, {
        method: "POST",
        body: formData,
      });

      console.log("Server responded with status:", response.status);

      if (!response.ok) {
        const text = await response.text();
        console.error("Server error response:", text);
        throw new Error("Transcription failed");
      }

      const data = await response.json();
      setText(data.transcription.trim());
      console.log("Transcription result:", data.transcription);
    } catch (err) {
      console.error("Transcription error:", err);
      setText("[Transcription failed]");
    }
  };

  const handleSubmit = () => {
    const inputContent = mode === 'image' ? image : capturedImage;
    setChatHistory(prev => [...prev, { role: 'user', text, image: inputContent }]);

    chat_inference();

    setText("");
  };

  const toBase64 = (blob) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onload = () => resolve(reader.result);
      reader.onerror = (error) => reject(error);
    });
    
  const chat_inference = async () => {
    try {
      const conversation = await Promise.all(
        chatHistory.map(async (entry, index) => {
          let base64Images = [];

          if (entry.image && typeof entry.image === "string" && entry.image.startsWith("blob:")) {
            try {
              const blob = await fetch(entry.image).then((res) => res.blob());
              const base64 = await toBase64(blob);
              base64Images = [base64];
            } catch (err) {
              console.warn(`Failed to convert blob at entry ${index}:`, err);
            }
          }

          return {
            role: entry.role,
            message: entry.text,
            images: base64Images,
          };
        })
      );    

      const payload = {
      learner_context: "learnerContext",
      conversation: conversation,
    };

      const response = await fetch(API_ENDPOINTS.INFERENCE, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload)
      });

      console.log("Server responded with status:", response.status);

      if (!response.ok) {
        const text = await response.text();
        console.error("Server error response:", text);
        throw new Error("Inference failed");
      }

      const data = await response.json();
      console.log("Inference result:", data);
      
      setChatHistory(prev => [...prev, { role: 'assistant', text: `${data.explanation.trim()} \n\n\n Flashcard ${data.flashcard_contents.trim()}` }]);
      
      setFlashcard(data.flashcard_contents.trim());

    } catch (err) {
      console.error("Inference error:", err);
    }
  }

  const dismissFlashcard = () => {
    setFlashcard(null);
  };

  return (
    <div className="app-container">
      {showFlash && <div className="flash-overlay"></div>}
      <div className="app-content">
        <div className="main-panel">
          <h1 className="heading">Evolving AI LMS</h1>
          {!mode && (
            <div className="mode-selector">
              <Button onClick={() => setMode('camera')}><Camera className="icon" /> Use Camera</Button>
              <Button onClick={() => setMode('image')}><ImageIcon className="icon" /> Upload Image</Button>
            </div>
          )}

          {mode === 'camera' && (
            <CameraPanel
              capturedImage={capturedImage}
              videoRef={videoRef}
              canvasRef={canvasRef}
              startCamera={startCamera}
              captureImage={captureImage}
              setCapturedImage={setCapturedImage}
              flashcard={flashcard}
              dismissFlashcard={dismissFlashcard}
            />
          )}

          {mode === 'image' && (
            <ImageUploader
              image={image}
              handleImageUpload={handleImageUpload}
              flashcard={flashcard}
              dismissFlashcard={dismissFlashcard}
            />
          )}
          <div className="controls-with-visualizer">
            <ControlsPanel
              text={text}
              listening={listening}
              transcribing={transcribing}
              startRecording={startRecording}
              stopRecording={stopRecording}
              handleSubmit={handleSubmit}
            />
            {listening && <Visualizer volume={volume} />}
          </div>
        </div>
        <ChatPanel chatHistory={chatHistory} />
      </div>
    </div>
  );
}


