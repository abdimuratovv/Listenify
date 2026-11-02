import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Headphones,
  Search,
  LockKeyhole,
  Play,
} from "lucide-react";
import { api } from "./api";
import { LEVELS, time, type User, type Material } from "./types";
import { Empty, PageTitle } from "./ui";

export default function Library({
  user,
  open,
  report,
}: {
  user: User;
  open: (id: string) => void;
  report: (s: string) => void;
}) {
  const [items, setItems] = useState<Material[]>([]),
    [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(""),
    [level, setLevel] = useState("");
  useEffect(() => {
    let active = true;
    setLoading(true);
    api<Material[]>(`materials?q=${encodeURIComponent(query)}&level=${level}`)
      .then((result) => {
        if (active) setItems(result);
      })
      .catch((e) => {
        if (active) report(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [query, level, report]);
  return (
    <>
      <PageTitle
        eyebrow="YOUR DAILY DOSE OF ENGLISH"
        title={`Salom, ${user.name.split(" ")[0]}.`}
        subtitle="Bugun qaysi hikoyadan boshlaymiz?"
        aside={
          <div className="quiet-label">
            <span className="live-dot" /> O‘z maromingizda
          </div>
        }
      />
      <section className="library-hero glass">
        <div className="hero-copy">
          <span className="eyebrow">TINGLASHDAN BOSHLANADI</span>
          <h2>
            Katta o‘zgarishlar.
            <br />
            Kichik tinglashlardan.
          </h2>
          <p>
            Darajangizga mos audioni tanlang.
            <br />
            Tinglang, takrorlang va ovozingizni yozib ko‘ring.
          </p>
          <button
            className="primary"
            disabled={!items.length}
            onClick={() => open(items[0].id)}
          >
            Mashqni boshlash <ArrowUpRight size={18} />
          </button>
        </div>
        <div className="hero-mark">
          <Headphones size={135} strokeWidth={0.6} />
          <span>
            FIND YOUR
            <br />
            <b>OWN VOICE.</b>
          </span>
        </div>
        <span className="hero-index">LISTENIFY / EVERYDAY PRACTICE</span>
      </section>
      <div className="library-tools">
        <div>
          <span className="eyebrow">THE COLLECTION</span>
          <h2>
            Audio kutubxona{" "}
            <span>{items.length.toString().padStart(2, "0")}</span>
          </h2>
        </div>
        <div className="segments glass">
          <button
            className={!level ? "active" : ""}
            onClick={() => setLevel("")}
          >
            Barchasi
          </button>
          {LEVELS.map((l) => (
            <button
              className={level === l ? "active" : ""}
              key={l}
              onClick={() => setLevel(l)}
              disabled={user.blocked_levels.includes(l)}
            >
              {user.blocked_levels.includes(l) && <LockKeyhole size={11} />}
              {l.replace("-", "–")}
            </button>
          ))}
        </div>
      </div>
      <label className="search glass">
        <Search size={17} />
        <input
          aria-label="Audioni qidirish"
          placeholder="Keyingi hikoyangizni toping…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <kbd>QIDIRUV</kbd>
      </label>
      {loading ? (
        <div className="loading" role="status">
          Kutubxona yuklanmoqda…
        </div>
      ) : !items.length ? (
        <Empty
          title={
            query || level
              ? "Mos audio topilmadi"
              : "Hikoyalar shu yerda boshlanadi"
          }
        >
          {query || level
            ? "Qidiruv yoki daraja filtrini o‘zgartirib ko‘ring."
            : user.role === "admin"
              ? "Admin bo‘limida birinchi audio va uning skriptini yuklang."
              : "Admin audio joylagach, ruxsat etilgan materiallar shu yerda ko‘rinadi."}
        </Empty>
      ) : (
        <div className="audio-grid">
          {items.map((item, index) => (
            <button
              className="audio-card glass"
              key={item.id}
              onClick={() => open(item.id)}
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <div className={`cover cover-${index % 3}`}>
                <span className="cover-index">
                  LISTENIFY / {String(index + 1).padStart(2, "0")}
                </span>
                <div className="vinyl-disc">
                  <div />
                </div>
                <span className="cover-time">{time(item.duration)}</span>
                <span className="cover-play">
                  <Play size={19} fill="currentColor" />
                </span>
              </div>
              <div className="card-body">
                <div className="card-kicker">
                  {item.level.replace("-", "–")} <span>·</span> V{item.number}
                  {item.status !== "published" && <span>{item.status}</span>}
                </div>
                <h3>{item.title}</h3>
                <div className="card-bottom">
                  <span>
                    <Headphones size={13} /> {item.count} marta to‘liq
                    tinglangan
                  </span>
                  <ArrowUpRight size={17} />
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
      <div className="page-foot">
        <span>Bir tinglash. Bir qadam oldinga.</span>
        <span>LISTEN / REPEAT / GROW</span>
      </div>
    </>
  );
}
