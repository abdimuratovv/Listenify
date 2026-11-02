import { useEffect, useRef, useState } from "react";
import {
  Mic,
  Square,
  RotateCcw,
  Upload,
  Check,
  ArrowUpRight,
} from "lucide-react";
import { api } from "./api";
import { time } from "./types";

export default function Recorder({
  version,
  pause,
  saved,
  report,
}: {
  version: string;
  pause: () => void;
  saved: () => void;
  report: (text: string) => void;
}) {
  const recorder = useRef<MediaRecorder | null>(null),
    stream = useRef<MediaStream | null>(null);
  const blob = useRef<Blob | null>(null),
    uploadKey = useRef(""),
    mounted = useRef(true),
    starting = useRef(false);
  const [recording, setRecording] = useState(false),
    [preview, setPreview] = useState(""),
    [seconds, setSeconds] = useState(0);
  const [busy, setBusy] = useState(false),
    [isSaved, setIsSaved] = useState(false),
    [requesting, setRequesting] = useState(false);
  const dirty = useRef(false);
  useEffect(() => {
    mounted.current = true;
    const before = (e: BeforeUnloadEvent) => {
      if (dirty.current) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    const navigation = (e: Event) => {
      if (
        dirty.current &&
        !confirm("Saqlanmagan yozuv yo‘qoladi. Sahifadan chiqasizmi?")
      )
        e.preventDefault();
    };
    window.addEventListener("beforeunload", before);
    window.addEventListener("listenify-navigate", navigation);
    return () => {
      mounted.current = false;
      window.removeEventListener("beforeunload", before);
      window.removeEventListener("listenify-navigate", navigation);
      recorder.current?.state === "recording" && recorder.current.stop();
      stream.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );
  useEffect(() => {
    if (!recording) return;
    const start = Date.now();
    const timer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - start) / 1000);
      setSeconds(elapsed);
      if (elapsed >= 600) recorder.current?.stop();
    }, 250);
    return () => clearInterval(timer);
  }, [recording]);

  async function start() {
    if (starting.current || recording) return;
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      report(
        "Brauzer mikrofon yozishni qo‘llamaydi. HTTPS yoki localhost va yangilangan brauzer kerak.",
      );
      return;
    }
    starting.current = true;
    setRequesting(true);
    try {
      pause();
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      if (!mounted.current) {
        mediaStream.getTracks().forEach((t) => t.stop());
        return;
      }
      stream.current = mediaStream;
      const mimeType = [
        "audio/webm;codecs=opus",
        "audio/mp4",
        "audio/webm",
        "audio/ogg;codecs=opus",
      ].find((t) => MediaRecorder.isTypeSupported(t));
      const instance = new MediaRecorder(
        mediaStream,
        mimeType ? { mimeType } : undefined,
      );
      recorder.current = instance;
      const chunks: BlobPart[] = [];
      let bytes = 0;
      instance.ondataavailable = (event) => {
        if (event.data.size) {
          chunks.push(event.data);
          bytes += event.data.size;
          if (bytes > 49 * 1024 * 1024 && instance.state === "recording")
            instance.stop();
        }
      };
      instance.onstop = () => {
        mediaStream.getTracks().forEach((t) => t.stop());
        if (!mounted.current) return;
        blob.current = new Blob(chunks, { type: instance.mimeType });
        uploadKey.current = crypto.randomUUID();
        setPreview(URL.createObjectURL(blob.current));
        setRecording(false);
        dirty.current = true;
      };
      instance.onerror = () => {
        mediaStream.getTracks().forEach((t) => t.stop());
        if (mounted.current) {
          setRecording(false);
          report("Ovoz yozishda xato yuz berdi. Qayta urinib ko‘ring.");
        }
      };
      blob.current = null;
      setPreview("");
      setIsSaved(false);
      setSeconds(0);
      dirty.current = true;
      instance.start(1000);
      setRecording(true);
    } catch (e) {
      stream.current?.getTracks().forEach((t) => t.stop());
      report(
        (e as DOMException).name === "NotAllowedError"
          ? "Mikrofon ruxsati berilmadi. Brauzer sozlamalarida ruxsatni oching."
          : "Mikrofon topilmadi yoki band. Qurilmani tekshiring.",
      );
    } finally {
      starting.current = false;
      if (mounted.current) setRequesting(false);
    }
  }
  async function upload() {
    if (!blob.current) return;
    setBusy(true);
    const form = new FormData();
    form.append("audio", blob.current, "recording");
    form.append("version_id", version);
    form.append("upload_key", uploadKey.current);
    try {
      await api("recordings", "POST", form);
      dirty.current = false;
      setIsSaved(true);
    } catch (e) {
      report(
        (e as Error).message +
          " Yozuv sahifada saqlanib turibdi; qayta urinishingiz mumkin.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className={`recorder glass ${recording ? "is-recording" : ""}`}>
      <div className="recorder-heading">
        <span className={`recorder-icon ${recording ? "pulsing" : ""}`}>
          <Mic size={24} />
        </span>
        <div>
          <span className="eyebrow">YOUR TURN</span>
          <h3>
            {recording
              ? "Sizni tinglayapmiz…"
              : isSaved
                ? "Ovozingiz saqlandi."
                : preview
                  ? "Yozuvingizni tinglab ko‘ring."
                  : "Endi navbat sizga."}
          </h3>
          <p>
            {recording
              ? `${time(seconds)} / 10:00 · tugatish uchun to‘xtating`
              : isSaved
                ? "Tekshirishga yuborish — My Records’da sizning tanlovingiz."
                : "Butun hikoyani yoki uning bir qismini o‘z ovozingizda takrorlang."}
          </p>
        </div>
      </div>
      {recording ? (
        <button
          className="stop-button"
          onClick={() => recorder.current?.stop()}
        >
          <Square size={15} fill="currentColor" /> To‘xtatish
        </button>
      ) : isSaved ? (
        <button className="primary" onClick={saved}>
          <Check size={16} /> My Records <ArrowUpRight size={16} />
        </button>
      ) : !preview ? (
        <button className="primary" onClick={start} disabled={requesting}>
          <Mic size={17} />
          {requesting ? "Ruxsat kutilmoqda…" : "Ovoz yozish"}
        </button>
      ) : null}
      {preview && !recording && !isSaved && (
        <div className="record-preview">
          <audio controls src={preview} />
          <div>
            <button className="secondary" onClick={start} disabled={busy}>
              <RotateCcw size={16} /> Qayta yozish
            </button>
            <button className="primary" onClick={upload} disabled={busy}>
              <Upload size={16} /> {busy ? "Yuklanmoqda…" : "Saqlash"}
            </button>
          </div>
          <small>
            Faqat siz va adminlar tinglay oladi. Avtomatik tekshirishga
            yuborilmaydi.
          </small>
        </div>
      )}
    </section>
  );
}
