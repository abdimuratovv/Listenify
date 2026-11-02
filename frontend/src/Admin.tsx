import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  Plus,
  Users,
  Layers3,
  Clock3,
  Pencil,
  ShieldCheck,
  LockKeyhole,
  Unlock,
  Ban,
  Trash2,
  ArrowUpRight,
} from "lucide-react";
import { api } from "./api";
import {
  LEVELS,
  date,
  time,
  statusLabel,
  type User,
  type Group,
  type Material,
  type Recording,
} from "./types";
import { Empty, Modal, PageTitle } from "./ui";

type ListenResult = {
  user_id: string;
  user_name: string;
  group_name: string | null;
  material_id: string;
  title: string;
  number: number;
  level: string;
  count: number;
};
type Dialog = { kind: string; item?: any };
export default function Admin({
  me,
  report,
}: {
  me: User;
  report: (text: string) => void;
}) {
  const [tab, setTab] = useState("materials"),
    [users, setUsers] = useState<User[]>([]),
    [groups, setGroups] = useState<Group[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]),
    [records, setRecords] = useState<Recording[]>([]);
  const [overview, setOverview] = useState({
    students: 0,
    groups: 0,
    pending: 0,
  });
  const [listening, setListening] = useState<ListenResult[]>([]);
  const [dialog, setDialog] = useState<Dialog | null>(null),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string[]>([]),
    [filter, setFilter] = useState("submitted"),
    [student, setStudent] = useState(""),
    [groupFilter, setGroupFilter] = useState(""),
    [materialFilter, setMaterialFilter] = useState("");
  const [source, setSource] = useState<{
    script: string;
    audio_url: string;
  } | null>(null);
  const load = useCallback(async () => {
    try {
      const [u, g, m, r, o, l] = await Promise.all([
        api<User[]>("admin/users"),
        api<Group[]>("admin/groups"),
        api<Material[]>("materials"),
        api<Recording[]>("admin/recordings"),
        api<typeof overview>("admin/overview"),
        api<ListenResult[]>("admin/listening"),
      ]);
      setUsers(u);
      setGroups(g);
      setMaterials(m);
      setRecords(r);
      setOverview(o);
      setListening(l);
    } catch (e) {
      report((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [report]);
  useEffect(() => {
    void load();
  }, [load]);
  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    try {
      await fn();
      setDialog(null);
      setSelected([]);
      await load();
    } catch (e) {
      report((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function editMaterial(item: Material) {
    try {
      setDialog({ kind: "material", item: await api(`materials/${item.id}`) });
    } catch (e) {
      report((e as Error).message);
    }
  }
  async function review(record: Recording) {
    setSource(null);
    setDialog({ kind: "review", item: record });
    try {
      setSource(await api(`admin/recordings/${record.id}/source`));
    } catch (e) {
      report((e as Error).message);
    }
  }
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!dialog) return;
    const form = new FormData(e.currentTarget),
      values = Object.fromEntries(form);
    if (dialog.kind === "material") {
      const file = form.get("audio") as File;
      if (!file?.size) form.delete("audio");
      await act(() =>
        api(
          `admin/materials${dialog.item ? `/${dialog.item.id}` : ""}`,
          "POST",
          form,
        ),
      );
    } else if (dialog.kind === "group")
      await act(() =>
        api(
          `admin/groups${dialog.item ? `/${dialog.item.id}` : ""}`,
          dialog.item ? "PATCH" : "POST",
          { name: values.name },
        ),
      );
    else if (dialog.kind === "transfer")
      await act(() =>
        api("admin/transfer", "POST", {
          user_ids: selected,
          group_id: values.group_id ? Number(values.group_id) : null,
        }),
      );
    else if (dialog.kind === "review")
      await act(() =>
        api(
          `admin/recordings/${dialog.item.id}/review`,
          dialog.item.review ? "PATCH" : "POST",
          {
            score: Number(values.score),
            comment: values.comment,
            revision: dialog.item.review?.revision || 0,
          },
        ),
      );
    else if (dialog.kind === "delete-user")
      await act(() =>
        api(`admin/users/${dialog.item.id}`, "DELETE", {
          confirm_email: values.confirm_email,
        }),
      );
  }
  const shownRecords = records.filter(
    (r) =>
      (!filter || r.status === filter) &&
      (!student || r.user_id === student) &&
      (!groupFilter || String(r.group_id) === groupFilter) &&
      (!materialFilter || r.material_id === materialFilter),
  );
  const tabs: Record<string, string> = {
    materials: "Audiolar",
    users: "Foydalanuvchilar",
    groups: "Guruhlar",
    recordings: "Ovoz yozuvlari",
    listening: "Tinglashlar",
  };
  return (
    <>
      <PageTitle
        eyebrow="THE TEACHER’S SPACE"
        title="Rivojlanishga yo‘l oching."
        subtitle="Materiallar, o‘quvchilar va har bir ovoz ortidagi mehnat."
        aside={<ShieldCheck size={35} strokeWidth={1} />}
      />
      <div className="records-stats">
        <div className="glass">
          <Users size={19} />
          <b>{overview.students}</b>
          <span>O‘quvchilar</span>
        </div>
        <div className="glass">
          <Layers3 size={19} />
          <b>{overview.groups}</b>
          <span>Guruhlar</span>
        </div>
        <div className="glass">
          <Clock3 size={19} />
          <b>{overview.pending}</b>
          <span>Tekshirish navbatida</span>
        </div>
      </div>
      <div className="admin-tabs segments glass">
        {Object.entries(tabs).map(([key, label]) => (
          <button
            key={key}
            className={tab === key ? "active" : ""}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="loading">Boshqaruv ma’lumotlari yuklanmoqda…</div>
      ) : (
        <>
          <div className="section-title">
            <h2>{tabs[tab]}</h2>
            {tab === "materials" && (
              <button
                className="primary"
                onClick={() => setDialog({ kind: "material" })}
              >
                <Plus size={16} /> Audio qo‘shish
              </button>
            )}
            {tab === "groups" && (
              <button
                className="primary"
                onClick={() => setDialog({ kind: "group" })}
              >
                <Plus size={16} /> Guruh yaratish
              </button>
            )}
            {tab === "users" && (
              <button
                className="secondary"
                disabled={!selected.length}
                onClick={() => setDialog({ kind: "transfer" })}
              >
                Guruhga ko‘chirish ({selected.length}){" "}
                <ArrowUpRight size={16} />
              </button>
            )}
          </div>
          {tab === "materials" &&
            (!materials.length ? (
              <Empty title="Birinchi hikoyani joylang">
                Audio fayl, daraja va skript bilan kutubxonani boshlang.
              </Empty>
            ) : (
              <div className="table-wrap glass">
                <table>
                  <thead>
                    <tr>
                      <th>Material</th>
                      <th>Daraja</th>
                      <th>Davomiylik</th>
                      <th>Holat</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {materials.map((m) => (
                      <tr key={m.id}>
                        <td>
                          <strong>{m.title}</strong>
                          <small>Versiya {m.number}</small>
                        </td>
                        <td>{m.level}</td>
                        <td>{time(m.duration)}</td>
                        <td>
                          <span className="badge">{statusLabel[m.status]}</span>
                        </td>
                        <td>
                          <button
                            className="secondary"
                            onClick={() => editMaterial(m)}
                          >
                            <Pencil size={14} /> Tahrirlash
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          {tab === "listening" && (
            <>
              <label className="admin-user-filter">
                O‘quvchi
                <select
                  value={student}
                  onChange={(e) => setStudent(e.target.value)}
                >
                  <option value="">Barcha o‘quvchilar</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name}
                    </option>
                  ))}
                </select>
              </label>
              {!listening.filter((r) => !student || r.user_id === student)
                .length ? (
                <Empty title="Tasdiqlangan tinglashlar hali yo‘q">
                  O‘quvchi audioni to‘liq tinglagach, natija aynan shu versiya
                  uchun ko‘rinadi.
                </Empty>
              ) : (
                <div className="table-wrap glass">
                  <table>
                    <thead>
                      <tr>
                        <th>O‘quvchi</th>
                        <th>Guruh</th>
                        <th>Audio</th>
                        <th>Daraja</th>
                        <th>To‘liq tinglashlar</th>
                      </tr>
                    </thead>
                    <tbody>
                      {listening
                        .filter((r) => !student || r.user_id === student)
                        .map((r) => (
                          <tr key={r.user_id + r.material_id + r.number}>
                            <td>{r.user_name}</td>
                            <td>{r.group_name || "Mustaqil"}</td>
                            <td>
                              {r.title}
                              <small>Versiya {r.number}</small>
                            </td>
                            <td>{r.level}</td>
                            <td>{r.count}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
          {tab === "users" && (
            <div className="table-wrap glass">
              <table>
                <thead>
                  <tr>
                    <th>
                      <span className="sr-only">Tanlash</span>
                    </th>
                    <th>Foydalanuvchi</th>
                    <th>Guruh</th>
                    <th>Natijalar</th>
                    <th>Huquqlar</th>
                    <th>Amallar</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td>
                        {u.role === "student" && (
                          <input
                            aria-label={`${u.name}ni tanlash`}
                            type="checkbox"
                            checked={selected.includes(u.id)}
                            onChange={(e) =>
                              setSelected(
                                e.target.checked
                                  ? [...selected, u.id]
                                  : selected.filter((id) => id !== u.id),
                              )
                            }
                          />
                        )}
                      </td>
                      <td>
                        <strong>{u.name}</strong>
                        <small>{u.email}</small>
                        <span className={`badge ${u.active ? "" : "danger"}`}>
                          {u.role === "admin"
                            ? "Admin"
                            : u.active
                              ? "Faol"
                              : "Bloklangan"}
                        </span>
                      </td>
                      <td>{u.group_name || "Mustaqil"}</td>
                      <td>
                        {u.listens} tinglash<small>{u.recordings} yozuv</small>
                      </td>
                      <td>
                        <button
                          className="secondary"
                          onClick={() =>
                            setDialog({
                              kind: "restrictions",
                              item: { kind: "user", ...u },
                            })
                          }
                        >
                          <LockKeyhole size={13} /> Darajalar
                        </button>
                      </td>
                      <td>
                        <div className="row-actions">
                          <button
                            className="icon-button"
                            disabled={u.id === me.id}
                            onClick={() =>
                              setDialog({ kind: "block-user", item: u })
                            }
                            aria-label={`${u.name}: ${u.active ? "bloklash" : "blokdan chiqarish"}`}
                          >
                            <Ban size={16} />
                          </button>
                          <button
                            className="icon-button danger"
                            disabled={u.id === me.id}
                            onClick={() =>
                              setDialog({ kind: "delete-user", item: u })
                            }
                            aria-label={`${u.name}: hisobni o‘chirish`}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {tab === "groups" &&
            (!groups.length ? (
              <Empty title="Guruhlaringiz uchun joy">
                Yangi guruh yarating va mavjud o‘quvchilarni unga biriktiring.
              </Empty>
            ) : (
              <div className="group-grid">
                {groups.map((g) => (
                  <article className="glass group-card" key={g.id}>
                    <Users size={25} strokeWidth={1.2} />
                    <h3>{g.name}</h3>
                    <p>{g.students} o‘quvchi</p>
                    <div className="group-levels">
                      {LEVELS.map((l) => (
                        <span
                          key={l}
                          className={`badge ${g.blocked_levels.includes(l) ? "danger" : "graded"}`}
                        >
                          {l} {g.blocked_levels.includes(l) ? "yopiq" : "ochiq"}
                        </span>
                      ))}
                    </div>
                    <div className="row-actions">
                      <button
                        className="secondary"
                        onClick={() => setDialog({ kind: "group", item: g })}
                      >
                        <Pencil size={14} /> Nomini o‘zgartirish
                      </button>
                      <button
                        className="secondary"
                        onClick={() =>
                          setDialog({
                            kind: "restrictions",
                            item: { kind: "group", ...g },
                          })
                        }
                      >
                        <LockKeyhole size={14} /> Darajalar
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ))}
          {tab === "recordings" && (
            <>
              <div className="admin-filters">
                <label>
                  Holat
                  <select
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                  >
                    <option value="">Barcha saqlangan yozuvlar</option>
                    <option value="submitted">Tekshirish navbati</option>
                    <option value="saved">Yuborilmagan</option>
                    <option value="graded">Baholangan</option>
                  </select>
                </label>
                <label>
                  O‘quvchi
                  <select
                    value={student}
                    onChange={(e) => setStudent(e.target.value)}
                  >
                    <option value="">Barcha o‘quvchilar</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Guruh
                  <select
                    value={groupFilter}
                    onChange={(e) => setGroupFilter(e.target.value)}
                  >
                    <option value="">Barcha guruhlar</option>
                    {groups.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Audio
                  <select
                    value={materialFilter}
                    onChange={(e) => setMaterialFilter(e.target.value)}
                  >
                    <option value="">Barcha audiolar</option>
                    {materials.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.title}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              {!shownRecords.length ? (
                <Empty title="Hozircha yozuv yo‘q">
                  Tanlangan filtrlarga mos yozuvlar shu yerda ko‘rinadi.
                </Empty>
              ) : (
                <div className="record-list">
                  {shownRecords.map((r) => (
                    <article className="record-card glass" key={r.id}>
                      <div className="record-card-top">
                        <div>
                          <span className="eyebrow">
                            {r.user_name} · {date(r.created_at)}
                          </span>
                          <h3>
                            {r.title} <small>V{r.number}</small>
                          </h3>
                        </div>
                        <span className={`badge ${r.status}`}>
                          {statusLabel[r.status]}
                        </span>
                      </div>
                      <audio controls preload="none" src={r.audio_url} />
                      {r.review && (
                        <p className="review-snippet">
                          <b>{r.review.score} / 5</b> {r.review.comment}
                        </p>
                      )}
                      {r.status !== "saved" && (
                        <button className="primary" onClick={() => review(r)}>
                          {r.review ? "Bahoni tahrirlash" : "Yozuvni baholash"}{" "}
                          <ArrowUpRight size={16} />
                        </button>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}
      {dialog && (
        <Modal
          title={
            (
              {
                material: dialog.item ? "Materialni tahrirlash" : "Yangi audio",
                group: dialog.item ? "Guruh nomi" : "Yangi guruh",
                transfer: "Guruhga ko‘chirish",
                review: "Ovozga e’tibor bering.",
                restrictions: "Daraja cheklovlari",
                "block-user": dialog.item?.active
                  ? "Hisobni bloklash"
                  : "Hisobni ochish",
                "delete-user": "Hisobni butunlay o‘chirish",
              } as Record<string, string>
            )[dialog.kind]
          }
          close={() => !busy && setDialog(null)}
        >
          <form onSubmit={submit}>
            {dialog.kind === "material" && (
              <>
                <label>
                  Sarlavha
                  <input
                    name="title"
                    defaultValue={dialog.item?.title}
                    maxLength={180}
                    required
                  />
                </label>
                <label>
                  Tavsif
                  <textarea
                    name="description"
                    defaultValue={dialog.item?.description}
                    maxLength={5000}
                  />
                </label>
                <div className="form-row">
                  <label>
                    Daraja
                    <select name="level" defaultValue={dialog.item?.level}>
                      {LEVELS.map((l) => (
                        <option key={l}>{l}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Holat
                    <select
                      name="status"
                      defaultValue={dialog.item?.status || "draft"}
                    >
                      {["draft", "published", "archived"].map((s) => (
                        <option value={s} key={s}>
                          {statusLabel[s]}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <label>
                  Audio fayl
                  <input
                    type="file"
                    name="audio"
                    accept="audio/*,.webm,.mp4,.ogg"
                    required={!dialog.item}
                  />
                  <small>
                    100 MiB gacha · 30 daqiqa gacha.{" "}
                    {dialog.item && "Bo‘sh qoldirsangiz joriy fayl saqlanadi."}
                  </small>
                </label>
                <label>
                  Audio skripti
                  <textarea
                    name="script"
                    defaultValue={dialog.item?.script}
                    rows={7}
                    maxLength={50000}
                    required
                  />
                </label>
                {dialog.item && (
                  <p className="notice">
                    Audio, skript yoki daraja o‘zgarsa yangi versiya yaratiladi.
                    Oldingi natija va yozuvlar saqlanadi.
                  </p>
                )}
              </>
            )}
            {dialog.kind === "group" && (
              <label>
                Guruh nomi
                <input
                  name="name"
                  defaultValue={dialog.item?.name}
                  maxLength={120}
                  required
                />
              </label>
            )}
            {dialog.kind === "transfer" && (
              <>
                <p>
                  Tanlangan o‘quvchilar:{" "}
                  <b>
                    {users
                      .filter((u) => selected.includes(u.id))
                      .map((u) => u.name)
                      .join(", ")}
                  </b>
                </p>
                <label>
                  Yangi guruh
                  <select name="group_id">
                    <option value="">Guruhsiz — mustaqil</option>
                    {groups.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="notice">
                  Natijalar, yozuvlar va baholar saqlanadi. Yangi guruh
                  cheklovlari qo‘llanadi; shaxsiy cheklovlar saqlanadi.
                </p>
              </>
            )}
            {dialog.kind === "review" && (
              <>
                <p>
                  {dialog.item.user_name} · {dialog.item.title} · V
                  {dialog.item.number}
                </p>
                <label>
                  O‘quvchi yozuvi
                  <audio controls src={dialog.item.audio_url} />
                </label>
                {source && (
                  <details>
                    <summary>Asl audio va skript bilan solishtirish</summary>
                    <audio controls src={source.audio_url} />
                    <p className="source-script">{source.script}</p>
                  </details>
                )}
                <label>
                  Baho
                  <select
                    aria-label="Baho"
                    name="score"
                    defaultValue={dialog.item.review?.score || 5}
                  >
                    {[5, 4, 3, 2, 1].map((n) => (
                      <option key={n} value={n}>
                        {n} / 5
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Yozma izoh
                  <textarea
                    name="comment"
                    defaultValue={dialog.item.review?.comment}
                    rows={5}
                    maxLength={5000}
                    required
                  />
                </label>
              </>
            )}
            {dialog.kind === "restrictions" && (
              <>
                <p>
                  {dialog.item.name}. Shaxsiy va guruh cheklovlari birlashadi;
                  ikkala joyda ham ochiq bo‘lsagina daraja ochiladi.
                </p>
                {LEVELS.map((level) => {
                  const blocked = (
                    dialog.item.kind === "user"
                      ? dialog.item.personal_blocks
                      : dialog.item.blocked_levels
                  ).includes(level);
                  return (
                    <div className="restriction-row" key={level}>
                      <strong>{level}</strong>
                      <span>{blocked ? "Yopiq" : "Ochiq"}</span>
                      <button
                        type="button"
                        className="secondary"
                        disabled={busy}
                        onClick={() =>
                          act(() =>
                            api("admin/restrictions", "POST", {
                              kind: dialog.item.kind,
                              id: dialog.item.id,
                              level,
                              blocked: !blocked,
                            }),
                          )
                        }
                      >
                        {blocked ? (
                          <Unlock size={15} />
                        ) : (
                          <LockKeyhole size={15} />
                        )}
                        {blocked ? "Ochish" : "Yopish"}
                      </button>
                    </div>
                  );
                })}
              </>
            )}
            {dialog.kind === "block-user" && (
              <>
                <p>
                  {dialog.item.name} ({dialog.item.email}){" "}
                  {dialog.item.active
                    ? "bloklanadi. Barcha faol sessiyalari tugatiladi. Ma’lumotlari saqlanadi."
                    : "hisobiga qayta kira oladi. Oldingi sessiyalar tiklanmaydi."}
                </p>
                <button
                  type="button"
                  className="primary"
                  disabled={busy}
                  onClick={() =>
                    act(() =>
                      api(`admin/users/${dialog.item.id}`, "PATCH", {
                        active: !dialog.item.active,
                      }),
                    )
                  }
                >
                  Tasdiqlash
                </button>
              </>
            )}
            {dialog.kind === "delete-user" && (
              <>
                <p className="error">
                  {dialog.item.name} hisobi, shaxsiy natijalari va ovoz
                  yozuvlari o‘chiriladi. Bu amal qaytarilmaydi.
                </p>
                <label>
                  Tasdiqlash uchun {dialog.item.email} ni yozing
                  <input
                    name="confirm_email"
                    type="email"
                    required
                    autoComplete="off"
                  />
                </label>
              </>
            )}
            {!["restrictions", "block-user"].includes(dialog.kind) && (
              <div className="modal-actions">
                <button
                  className="secondary"
                  type="button"
                  disabled={busy}
                  onClick={() => setDialog(null)}
                >
                  Bekor qilish
                </button>
                <button className="primary" disabled={busy}>
                  {busy
                    ? "Saqlanmoqda…"
                    : dialog.kind === "delete-user"
                      ? "Hisobni o‘chirish"
                      : "Saqlash"}
                  <ArrowUpRight size={16} />
                </button>
              </div>
            )}
          </form>
        </Modal>
      )}
    </>
  );
}
