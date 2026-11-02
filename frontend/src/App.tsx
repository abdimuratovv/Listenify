import {
  useCallback,
  useEffect,
  useState,
  useRef,
  useLayoutEffect,
} from "react";
import {
  BookOpen,
  Mic2,
  ShieldCheck,
  LogOut,
  ArrowUpRight,
  AudioLines,
  Accessibility,
  X,
  ChevronRight,
} from "lucide-react";
import { api } from "./api";
import type { User } from "./types";
import { Brand } from "./ui";
import Auth from "./Auth";
import Library from "./Library";
import Player from "./Player";
import Records from "./Records";
import Admin from "./Admin";

export default function App() {
  const [user, setUser] = useState<User | null>(null),
    [loading, setLoading] = useState(true),
    [failure, setFailure] = useState("");
  const [consoleEmail, setConsoleEmail] = useState(true),
    [view, setView] = useState("library"),
    [material, setMaterial] = useState("");
  const [toast, setToast] = useState(""),
    [accessible, setAccessible] = useState(
      () => localStorage.getItem("listenify-accessible") === "1",
    );
  const nav = useRef<HTMLElement>(null);
  const [lens, setLens] = useState({ left: 0, top: 0, width: 0, height: 0 });
  useLayoutEffect(() => {
    const element = nav.current;
    if (!element) return;
    const measure = () => {
      const button = element.querySelector<HTMLButtonElement>("button.active");
      if (button)
        setLens({
          left: button.offsetLeft,
          top: button.offsetTop,
          width: button.offsetWidth,
          height: button.offsetHeight,
        });
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [view, user?.id]);
  const report = useCallback((text: string) => setToast(text), []);
  const refresh = useCallback(async () => {
    try {
      const data = await api("session");
      setUser(data.user);
      setConsoleEmail(data.email_delivery === "console");
      setFailure("");
    } catch {
      setFailure(
        "Serverga ulanib bo‘lmadi. Backend ishlayotganini tekshiring.",
      );
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void refresh();
    const expired = () => {
      setUser(null);
      report("Sessiya tugagan. Qayta hisobingizga kiring.");
    };
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, [refresh, report]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 9000);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    document.documentElement.classList.toggle("accessible", accessible);
    localStorage.setItem("listenify-accessible", accessible ? "1" : "0");
  }, [accessible]);
  function navigate(next: string, id?: string) {
    if (
      !window.dispatchEvent(
        new Event("listenify-navigate", { cancelable: true }),
      )
    )
      return;
    if (id) setMaterial(id);
    setView(next);
    window.scrollTo({ top: 0, behavior: accessible ? "instant" : "smooth" });
    void refresh();
  }
  async function signOut() {
    if (
      !window.dispatchEvent(
        new Event("listenify-navigate", { cancelable: true }),
      )
    )
      return;
    try {
      await api("auth/logout", "POST");
      setUser(null);
      setView("library");
    } catch (e) {
      report((e as Error).message);
    }
  }
  if (loading)
    return (
      <div className="boot">
        <AudioLines size={36} />
        <p>Listenify yuklanmoqda…</p>
      </div>
    );
  if (failure)
    return (
      <div className="boot">
        <p role="alert">{failure}</p>
        <button className="primary" onClick={refresh}>
          Qayta urinish
        </button>
      </div>
    );
  const names: Record<string, string> = {
    library: "Kutubxona",
    records: "My Records",
    audio: "Tinglash maydoni",
    admin: "Admin maydoni",
  };
  return (
    <>
      {!user ? (
        <Auth
          consoleEmail={consoleEmail}
          done={(u) => {
            setUser(u);
            setView("library");
          }}
        />
      ) : (
        <div
          className={`app-shell theme-${view === "records" ? "records" : "library"}`}
        >
          <div className="app-wallpaper" />
          <aside className="sidebar glass">
            <Brand />
            <span className="side-label">SHAXSIY MAYDON</span>
            <nav ref={nav} aria-label="Asosiy navigatsiya">
              <span
                className="nav-lens"
                aria-hidden="true"
                style={{
                  width: lens.width,
                  height: lens.height,
                  transform: `translate(${lens.left}px, ${lens.top}px)`,
                }}
              />
              <button
                className={
                  view === "library" || view === "audio" ? "active" : ""
                }
                aria-current={
                  view === "library" || view === "audio" ? "page" : undefined
                }
                onClick={() => navigate("library")}
              >
                <BookOpen size={19} />
                Kutubxona
                <ChevronRight className="nav-chevron" size={14} />
              </button>
              <button
                className={view === "records" ? "active" : ""}
                aria-current={view === "records" ? "page" : undefined}
                onClick={() => navigate("records")}
              >
                <Mic2 size={19} />
                My Records
                <ChevronRight className="nav-chevron" size={14} />
              </button>
              {user.role === "admin" && (
                <>
                  <span className="side-label admin-side-label">BOSHQARUV</span>
                  <button
                    className={view === "admin" ? "active" : ""}
                    aria-current={view === "admin" ? "page" : undefined}
                    onClick={() => navigate("admin")}
                  >
                    <ShieldCheck size={19} />
                    Admin maydoni
                    <ChevronRight className="nav-chevron" size={14} />
                  </button>
                </>
              )}
            </nav>
            <div className="sidebar-note">
              <AudioLines size={24} strokeWidth={1.1} />
              <p>
                O‘z ovozingizni
                <br />
                <b>toping.</b>
              </p>
              <span>Bir tinglashdan boshlang.</span>
            </div>
            <div className="sidebar-bottom">
              <div className="group-info">
                <span className="eyebrow">SIZNING GURUHINGIZ</span>
                <p>
                  {user.group_name || "Mustaqil o‘quvchi"}
                  <ArrowUpRight size={13} />
                </p>
              </div>
              <div className="profile">
                <span className="avatar">
                  {user.name
                    .split(" ")
                    .map((n) => n[0])
                    .slice(0, 2)
                    .join("")}
                </span>
                <div>
                  <strong>{user.name}</strong>
                  <small>
                    {user.role === "admin" ? "Administrator" : "O‘quvchi"}
                  </small>
                </div>
                <button
                  className="icon-button"
                  onClick={signOut}
                  aria-label="Hisobdan chiqish"
                >
                  <LogOut size={16} />
                </button>
              </div>
            </div>
          </aside>
          <main className="main">
            <header className="topbar">
              <div>
                Shaxsiy maydon <ChevronRight size={12} />
                <b>{names[view]}</b>
              </div>
              <div className="topbar-right">
                <span className="topbar-motto">A LITTLE EVERY DAY.</span>
                <button
                  className="icon-button glass mobile-logout"
                  onClick={signOut}
                  aria-label="Hisobdan chiqish"
                >
                  <LogOut size={17} />
                </button>
                <button
                  className="icon-button glass"
                  aria-label="Harakat va shaffoflikni kamaytirish"
                  aria-pressed={accessible}
                  onClick={() => setAccessible(!accessible)}
                >
                  <Accessibility size={18} />
                </button>
              </div>
            </header>
            <div
              className="content"
              key={view + (view === "audio" ? material : "")}
            >
              {view === "library" && (
                <Library
                  user={user}
                  open={(id) => navigate("audio", id)}
                  report={report}
                />
              )}
              {view === "audio" && (
                <Player
                  id={material}
                  back={() => navigate("library")}
                  records={() => navigate("records")}
                  report={report}
                />
              )}
              {view === "records" && <Records report={report} />}
              {view === "admin" && user.role === "admin" && (
                <Admin me={user} report={report} />
              )}
            </div>
          </main>
        </div>
      )}
      {toast && (
        <div className="toast glass" role="alert">
          <p>{toast}</p>
          <button
            className="icon-button"
            onClick={() => setToast("")}
            aria-label="Xabarni yopish"
          >
            <X size={17} />
          </button>
        </div>
      )}
    </>
  );
}
