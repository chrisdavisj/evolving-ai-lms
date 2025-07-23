import express from "express";
import cors from "cors";
import { execFile } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import multer from "multer";
import fs from "fs";
import ffmpeg from "fluent-ffmpeg";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());

const upload = multer({ dest: "uploads/" });

app.post("/api/transcribe", upload.single("audio"), (req, res) => {
  if (!req.file) {
    return res.status(400).send("No audio file uploaded");
  }

  const audioPath = req.file.path;
  const wavPath = `${audioPath}.wav`;
  const whisperBinary = path.resolve(__dirname, "../whisper-local/build/bin/whisper-cli");
  const modelPath = path.resolve(__dirname, "../whisper-local/models/ggml-base.en.bin");

  ffmpeg(audioPath)
    .toFormat("wav")
    .on("end", () => {

      execFile(
        whisperBinary,
        ["-m", modelPath, "-f", wavPath, "-otxt"],
        (error, stdout, stderr) => {
          
          if (error) {
            console.error("Whisper execFile error:", error);
            cleanup();
            return res.status(500).send("Transcription failed");
          }

          try {
            const transcription = fs.readFileSync(`${wavPath}.txt`, "utf-8");
            res.json({ transcription });
          } catch (readErr) {
            console.error("Failed to read transcription file:", readErr);
            res.status(500).send("Failed to read transcription");
          } finally {
            cleanup();
          }
        }
      );
    })
    .on("error", (err) => {
      console.error("FFmpeg error:", err);
      cleanup();
      res.status(500).send("Audio conversion failed");
    })
    .save(wavPath);

  function cleanup() {
    [audioPath, wavPath, `${wavPath}.txt`].forEach((file) => {
      if (fs.existsSync(file)) {
        try {
          fs.unlinkSync(file);
        } catch (e) {
          console.warn(`Failed to delete ${file}:`, e);
        }
      }
    });
  }
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});