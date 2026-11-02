import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Play,
  Pause,
  RotateCcw,
  Volume2,
  Eye,
  EyeOff,
  CheckCircle2,
  Headphones,
} from "lucide-react";
import { api } from "./api";
import { time, type Material } from "./types";
import { useListening } from "./useListening";
import Recorder from "./Recorder";

export default function Player({
  id,
  back,
  records,
  report,
}: {
  id: string;
  back: () => void;
  records: () => void;
  report: (text: string) => void;
}) {
  const [material, setMaterial] = useState<Material | null>(null),
    [failed, setFailed] = useState("");
  useEffect(() => {
    let active = true;
    api<Material>(`materials/${id}`)
      .then((item) => {
        if (active) setMaterial(item);
      })
      .catch((e) => {
        if (active) setFailed(e.message);
      });
    return () => {
      active = false;
    };
  }, [id]);
  if (failed)
    return (
      <div className="empty glass">
        <h2>{failed}</h2>
        <button className="secondary" onClick={back}>
          Kutubxonaga qaytish
        </button>
      </div>
    );
  if (!material)
    return (
      <div className="loading" role="status">
        Audio yuklanmoqda…
      </div>
    );
  return (
    <PlayerContent
      key={material.version_id}
      material={material}
      back={back}
      records={records}
      report={report}
    />
  );
}

function PlayerContent({
  material,
  back,
  records,
  report,
}: {
  material: Material;
  back: () => void;
  records: () => void;
  report: (text: string) => void;
}) {
  const audio = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false),
    [position, setPosition] = useState(0),
    [volume, setVolume] = useState(1);
  const [showScript, setShowScript] = useState(true),
    [count, setCount] = useState(material.count),
    [busy, setBusy] = useState(false);
  const listening = useListening(material.version_id, audio, setCount);
  useEffect(() => {
    const element = audio.current;
    return () => {
      element?.pause();
    };
  }, []);
  return (
    <>
      <button className="back-button" onClick={back}>
        <ArrowLeft size={16} /> Kutubxonaga qaytish
      </button>
      <div className="page-heading">
        <div>
          <span className="eyebrow">
            {material.level.replace("-", "–")} / LISTENING PRACTICE / V
            {material.number}
          </span>
          <h1>{material.title}</h1>
          <p>
            {material.description ||
              "Tinglang. His qiling. O‘z ovozingizda takrorlang."}
          </p>
        </div>
        <span className="quiet-label">
          <Headphones size={15} /> {time(material.duration)}
        </span>
      </div>
      <div className="player-layout">
        <section className={`player glass ${playing ? "playing" : ""}`}>
          <audio
            ref={audio}
            src={material.audio_url}
            preload="metadata"
            onTimeUpdate={(e) => setPosition(e.currentTarget.currentTime)}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onEnded={() => setPlaying(false)}
            onError={() =>
              report(
                "Audio yuklanmadi. Ulanish yoki kirish huquqini tekshiring.",
              )
            }
          />
          <div className="player-art">
            <div className="large-disc">
              <div className="disc-label">
                <Headphones size={30} strokeWidth={1} />
                <span>LISTENIFY</span>
                <i />
              </div>
            </div>
            <span className="player-art-label">
              A STORY WORTH LISTENING TO.
            </span>
          </div>
          <div className="player-meta">
            <span className="eyebrow">NOW PLAYING</span>
            <h2>{material.title}</h2>
            <p>
              {material.level.replace("-", "–")} · {time(material.duration)}
            </p>
          </div>
          <label className="sr-only" htmlFor="audio-position">
            Ijro vaqti
          </label>
          <input
            id="audio-position"
            className="progress"
            type="range"
            min="0"
            max={material.duration}
            step="0.01"
            value={position}
            onChange={(e) => {
              audio.current!.currentTime = Number(e.target.value);
              setPosition(Number(e.target.value));
            }}
          />
          <div className="time-row">
            <span>{time(position)}</span>
            <span>{time(material.duration)}</span>
          </div>
          <div className="player-controls">
            <button
              className="icon-button"
              onClick={listening.restart}
              aria-label="Boshiga qaytish"
            >
              <RotateCcw size={21} />
            </button>
            <button
              className="play-main"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await listening.toggle();
                } finally {
                  setBusy(false);
                }
              }}
              aria-label={playing ? "Pauza" : "Ijro etish"}
            >
              {playing ? (
                <Pause size={25} fill="currentColor" />
              ) : (
                <Play size={25} fill="currentColor" />
              )}
            </button>
            <div className="volume">
              <Volume2 size={19} />
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                aria-label="Ovoz balandligi"
                value={volume}
                onChange={(e) => {
                  setVolume(Number(e.target.value));
                  audio.current!.volume = Number(e.target.value);
                }}
              />
            </div>
          </div>
          <div className="listen-count">
            <CheckCircle2 size={16} /> Siz {count} marta to‘liq tinglagansiz
          </div>
          <p className="listening-status" role="status">
            {listening.message}
          </p>
        </section>
        <section className="script-panel glass">
          <div className="script-heading">
            <span className="eyebrow">READ ALONG</span>
            <button
              className="icon-button"
              onClick={() => setShowScript(!showScript)}
              aria-label={showScript ? "Skriptni yashirish" : "Skriptni ochish"}
            >
              {showScript ? <Eye size={18} /> : <EyeOff size={18} />}
            </button>
          </div>
          <h2>Hikoya satrlarda.</h2>
          {showScript ? (
            <div className="script-text">
              {material.script?.split(/\n+/).map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          ) : (
            <div className="script-hidden">
              <Headphones size={35} strokeWidth={1} />
              <p>Faqat tinglashga e’tibor bering.</p>
            </div>
          )}
          <div className="script-foot">Har bir so‘zga quloq tuting.</div>
        </section>
      </div>
      <Recorder
        version={material.version_id}
        pause={() => audio.current?.pause()}
        saved={records}
        report={report}
      />
    </>
  );
}
