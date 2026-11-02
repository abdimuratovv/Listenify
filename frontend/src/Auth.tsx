import { useState, type FormEvent } from "react";
import { ArrowRight, Headphones, Mic, Check } from "lucide-react";
import { api } from "./api";
import { Brand } from "./ui";
import type { User } from "./types";

export default function Auth({
  done,
  consoleEmail,
}: {
  done: (user: User) => void;
  consoleEmail: boolean;
}) {
  const params = new URLSearchParams(location.search);
  const [mode, setMode] = useState(params.has("reset") ? "confirm" : "login");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    const values = Object.fromEntries(new FormData(e.currentTarget));
    try {
      const endpoint = mode === "confirm" ? "reset-confirm" : mode;
      const result = await api(`auth/${endpoint}`, "POST", {
        ...values,
        uid: params.get("reset"),
        token: params.get("token"),
      });
      if (result.user) done(result.user);
      else if (mode === "confirm") {
        setMode("login");
        history.replaceState({}, "", "/");
        setNotice("Parol yangilandi. Hisobingizga kiring.");
      } else
        setNotice(
          consoleEmail
            ? "Hisob mavjud bo‘lsa, tiklash havolasi lokal server terminalida chiqadi. Email jo‘natish hali ulanmagan."
            : "Hisob mavjud bo‘lsa, tiklash havolasi emailingizga yuboriladi.",
        );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const titles: Record<string, string> = {
    login: "Yana bir qadam\noldinga.",
    register: "O‘z ovozingizni\ntoping.",
    reset: "Qaytadan\nboshlaymiz.",
    confirm: "Yangi parol,\nyangi boshlanish.",
  };
  return (
    <div className="auth-page">
      <section className="auth-story">
        <Brand />
        <div className="story-body">
          <span className="eyebrow">LISTEN. REPEAT. BECOME.</span>
          <h1>
            Har bir tinglash —<br />
            yangi imkoniyat<span>.</span>
          </h1>
          <p>
            Ingliz tilini eshitishdan his qilishgacha.
            <br />
            O‘z maromingizda tinglang va mashq qiling.
          </p>
          <div className="story-steps">
            <span>
              <Headphones size={18} />
              Tinglang
            </span>
            <i />
            <span>
              <Mic size={18} />
              Takrorlang
            </span>
            <i />
            <span>
              <Check size={18} />
              Rivojlaning
            </span>
          </div>
        </div>
        <div className="story-bottom">
          <span>O‘Z OVOZINGIZNI TOPING</span>
          <span>01 / YOUR NEXT CHAPTER</span>
        </div>
      </section>
      <main className="auth-main">
        <div className="auth-form">
          <span className="eyebrow">SIZNING SHAXSIY MASHQ MAYDONINGIZ</span>
          <h2>{titles[mode]}</h2>
          <p>
            {mode === "login"
              ? "Davom etish uchun hisobingizga kiring."
              : mode === "register"
                ? "Birinchi qadamingizni bugun qo‘ying."
                : "Hisobingizga kirishni tiklang."}
          </p>
          <form onSubmit={submit}>
            {mode === "register" && (
              <label>
                Ismingiz
                <input
                  name="name"
                  placeholder="Ism va familiya"
                  autoComplete="name"
                  maxLength={120}
                  required
                />
              </label>
            )}
            {mode !== "confirm" && (
              <label>
                Email
                <input
                  name="email"
                  type="email"
                  placeholder="siz@example.com"
                  autoComplete="email"
                  maxLength={254}
                  required
                />
              </label>
            )}
            {mode !== "reset" && (
              <label>
                Parol
                <input
                  name="password"
                  type="password"
                  placeholder="Parolingiz"
                  minLength={mode === "login" ? 1 : 8}
                  maxLength={128}
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                  required
                />
              </label>
            )}
            {mode === "login" && (
              <button
                type="button"
                className="text-button forgot"
                onClick={() => {
                  setMode("reset");
                  setError("");
                }}
              >
                Parolni unutdingizmi?
              </button>
            )}
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
            {notice && (
              <p className="notice" role="status">
                {notice}
              </p>
            )}
            <button className="primary auth-submit" disabled={busy}>
              {busy
                ? "Kuting…"
                : mode === "login"
                  ? "Hisobga kirish"
                  : mode === "register"
                    ? "Hisob yaratish"
                    : mode === "reset"
                      ? "Tiklash havolasini olish"
                      : "Parolni yangilash"}
              <ArrowRight size={18} />
            </button>
          </form>
          <p className="auth-switch">
            {mode === "login" ? "Hali hisobingiz yo‘qmi?" : "Hisobingiz bormi?"}{" "}
            <button
              className="text-button"
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError("");
                setNotice("");
              }}
            >
              {mode === "login" ? "Ro‘yxatdan o‘tish" : "Hisobga kirish"}
            </button>
          </p>
          <div className="auth-note">
            <span className="live-dot" /> Shaxsiy mashqlar. Haqiqiy rivojlanish.
          </div>
        </div>
      </main>
    </div>
  );
}
