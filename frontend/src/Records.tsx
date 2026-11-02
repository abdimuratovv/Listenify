import { useEffect, useState } from "react";
import {
  Send,
  Trash2,
  CheckCircle2,
  Clock3,
  Mic,
  ArrowUpRight,
} from "lucide-react";
import { api } from "./api";
import { date, time, statusLabel, type Recording } from "./types";
import { Empty, Modal, PageTitle } from "./ui";

export default function Records({
  report,
}: {
  report: (text: string) => void;
}) {
  const [items, setItems] = useState<Recording[]>([]),
    [loading, setLoading] = useState(true);
  const [action, setAction] = useState<{
      kind: "submit" | "delete";
      record: Recording;
    } | null>(null),
    [busy, setBusy] = useState(false);
  async function load() {
    try {
      setItems(await api("recordings"));
    } catch (e) {
      report((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  async function confirmAction() {
    if (!action) return;
    setBusy(true);
    try {
      await api(
        `recordings/${action.record.id}${action.kind === "submit" ? "/submit" : ""}`,
        action.kind === "submit" ? "POST" : "DELETE",
      );
      setAction(null);
      await load();
    } catch (e) {
      report((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="YOUR VOICE, YOUR JOURNEY"
        title="My Records"
        subtitle="Har bir yozuv — o‘zingizga yaqinroq bir qadam."
        aside={<Mic size={38} strokeWidth={1} />}
      />
      <div className="records-stats">
        <div className="glass">
          <Mic size={19} />
          <b>{items.length.toString().padStart(2, "0")}</b>
          <span>Ovoz yozuvlari</span>
        </div>
        <div className="glass">
          <Clock3 size={19} />
          <b>
            {items
              .filter((r) => r.status === "submitted")
              .length.toString()
              .padStart(2, "0")}
          </b>
          <span>Tekshirishda</span>
        </div>
        <div className="glass">
          <CheckCircle2 size={19} />
          <b>
            {items
              .filter((r) => r.status === "graded")
              .length.toString()
              .padStart(2, "0")}
          </b>
          <span>Baholangan</span>
        </div>
      </div>
      <div className="section-title">
        <h2>Ovozingiz arxivi</h2>
        <span className="eyebrow">ONLY YOU & YOUR TEACHER</span>
      </div>
      {loading ? (
        <div className="loading">Yozuvlar yuklanmoqda…</div>
      ) : !items.length ? (
        <Empty title="Birinchi ovozingizni saqlang">
          Kutubxonadan audioni oching, tinglang va o‘z ovozingizda takrorlab
          yozing.
        </Empty>
      ) : (
        <div className="record-list">
          {items.map((record) => (
            <article key={record.id} className="record-card glass">
              <div className="record-card-top">
                <div>
                  <span className="eyebrow">
                    V{record.number} · {date(record.created_at)}
                  </span>
                  <h3>{record.title}</h3>
                  <span className="muted">{time(record.duration)}</span>
                </div>
                <span className={`badge ${record.status}`}>
                  {statusLabel[record.status]}
                </span>
              </div>
              <audio
                controls
                preload="none"
                src={record.audio_url}
                onError={() =>
                  report("Yozuv ijro etilmadi. Ulanishni tekshiring.")
                }
              />
              {record.status === "saved" && (
                <div className="record-actions">
                  <button
                    className="secondary"
                    onClick={() => setAction({ kind: "delete", record })}
                    aria-label={`${record.title} yozuvini o‘chirish`}
                  >
                    <Trash2 size={15} /> O‘chirish
                  </button>
                  <button
                    className="primary"
                    onClick={() => setAction({ kind: "submit", record })}
                  >
                    <Send size={15} /> Tekshirishga yuborish
                  </button>
                </div>
              )}
              {record.review && (
                <div className="feedback">
                  <div>
                    <span className="eyebrow">O‘QITUVCHI IZOHI</span>
                    <strong>
                      {record.review.score}
                      <small> / 5</small>
                    </strong>
                  </div>
                  <p>{record.review.comment}</p>
                  <small>
                    {record.review.reviewer} · {date(record.review.reviewed_at)}
                  </small>
                  {record.review.revision > 1 && (
                    <small className="edit-audit">
                      Tahrir: {record.review.editor} ·{" "}
                      {date(record.review.edited_at)}
                    </small>
                  )}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
      {action && (
        <Modal
          title={
            action.kind === "submit"
              ? "Tekshirishga yuborish"
              : "Yozuvni o‘chirish"
          }
          close={() => !busy && setAction(null)}
        >
          <p>
            “{action.record.title}”{" "}
            {action.kind === "submit"
              ? "yozuvi adminga yuboriladi. Yuborilgan nusxani o‘zgartirib yoki o‘chirib bo‘lmaydi. Yana mashq qilish uchun yangi yozuv yarating."
              : "yozuvi butunlay o‘chiriladi."}
          </p>
          <div className="modal-actions">
            <button
              className="secondary"
              disabled={busy}
              onClick={() => setAction(null)}
            >
              Bekor qilish
            </button>
            <button className="primary" disabled={busy} onClick={confirmAction}>
              {busy
                ? "Kuting…"
                : action.kind === "submit"
                  ? "Yuborish"
                  : "O‘chirish"}
              <ArrowUpRight size={16} />
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
