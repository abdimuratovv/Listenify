import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, cancelAttempt } from "./api";

export function useListening(
  version: string,
  audio: React.RefObject<HTMLAudioElement | null>,
  counted: (n: number) => void,
) {
  const attempt = useRef<string | null>(null),
    sequence = useRef(0),
    chain = useRef(Promise.resolve());
  const generation = useRef(0),
    seeking = useRef(false),
    buffering = useRef(false),
    alive = useRef(true);
  const [message, setMessage] = useState(
    "Hisob uchun audioni boshidan to‘liq tinglang.",
  );
  const countedRef = useRef(counted);
  countedRef.current = counted;
  const fail = useCallback((text: string) => {
    attempt.current = null;
    if (alive.current) setMessage(text);
  }, []);
  const send = useCallback(
    (event: string, position: number) => {
      const id = attempt.current,
        epoch = generation.current;
      if (!id) return;
      chain.current = chain.current.then(async () => {
        if (id !== attempt.current || epoch !== generation.current) return;
        try {
          await api(`attempts/${id}/heartbeat`, "POST", {
            event,
            position,
            sequence: ++sequence.current,
          });
          if (event === "ended") {
            try {
              const result = await api<{ count: number }>(
                `attempts/${id}/finish`,
                "POST",
              );
              if (alive.current && epoch === generation.current) {
                countedRef.current(result.count);
                setMessage(
                  "To‘liq tinglash tasdiqlandi. Yana bir qadam oldinga!",
                );
              }
              attempt.current = null;
            } catch (e) {
              if (e instanceof ApiError && e.status === 409) {
                if (alive.current && epoch === generation.current)
                  setMessage(e.message);
              } else throw e;
            }
          }
        } catch (e) {
          if (epoch === generation.current)
            fail((e as Error).message + " Qayta boshidan boshlang.");
        }
      });
    },
    [fail],
  );

  useEffect(() => {
    alive.current = true;
    const element = audio.current!;
    const seek = () => {
      seeking.current = true;
      send("seek", element.currentTime);
    };
    const seeked = () => {
      seeking.current = false;
      send(element.paused ? "pause" : "play", element.currentTime);
    };
    const pause = () => {
      if (!element.ended && !seeking.current)
        send("pause", element.currentTime);
    };
    const playing = () => {
      buffering.current = false;
      if (!seeking.current) send("play", element.currentTime);
    };
    const waiting = () => {
      buffering.current = true;
      send("waiting", element.currentTime);
    };
    const ended = () => send("ended", element.currentTime);
    const rate = () => {
      if (element.playbackRate !== 1) {
        element.playbackRate = 1;
        fail("Ijro tezligi o‘zgargan. Hisob uchun boshidan boshlang.");
      }
    };
    const offline = () =>
      fail(
        "Tarmoq uzildi. Ijro davom etishi mumkin, ammo bu urinish hisoblanmaydi.",
      );
    const leave = () => {
      const id = attempt.current;
      generation.current++;
      attempt.current = null;
      if (id) cancelAttempt(id);
    };
    const timer = window.setInterval(() => {
      if (
        !element.paused &&
        !element.ended &&
        !seeking.current &&
        !buffering.current
      )
        send("tick", element.currentTime);
    }, 1000);
    element.addEventListener("seeking", seek);
    element.addEventListener("seeked", seeked);
    element.addEventListener("pause", pause);
    element.addEventListener("playing", playing);
    element.addEventListener("waiting", waiting);
    element.addEventListener("ended", ended);
    element.addEventListener("ratechange", rate);
    window.addEventListener("offline", offline);
    window.addEventListener("pagehide", leave);
    return () => {
      alive.current = false;
      leave();
      clearInterval(timer);
      element.removeEventListener("seeking", seek);
      element.removeEventListener("seeked", seeked);
      element.removeEventListener("pause", pause);
      element.removeEventListener("playing", playing);
      element.removeEventListener("waiting", waiting);
      element.removeEventListener("ended", ended);
      element.removeEventListener("ratechange", rate);
      window.removeEventListener("offline", offline);
      window.removeEventListener("pagehide", leave);
    };
  }, [version, audio, send, fail]);

  async function toggle() {
    const element = audio.current!;
    if (!element.paused) {
      element.pause();
      return;
    }
    await chain.current;
    if (
      element.ended ||
      (element.duration && element.currentTime >= element.duration - 0.01)
    )
      element.currentTime = 0;
    if (!attempt.current && element.currentTime < 0.1) {
      const epoch = generation.current;
      try {
        const result = await api<{ id: string }>(
          `versions/${version}/attempts`,
          "POST",
        );
        if (!alive.current || epoch !== generation.current) {
          cancelAttempt(result.id);
          return;
        }
        generation.current++;
        sequence.current = 0;
        attempt.current = result.id;
        chain.current = Promise.resolve();
        setMessage("To‘liq tinglash serverda tekshirilmoqda…");
      } catch (e) {
        fail((e as Error).message);
      }
    }
    try {
      await element.play();
    } catch {
      fail("Audio ijro etilmadi. Fayl yoki ulanishni tekshiring.");
    }
  }
  function restart() {
    const element = audio.current!;
    element.pause();
    if (attempt.current) cancelAttempt(attempt.current);
    generation.current++;
    attempt.current = null;
    element.currentTime = 0;
    setMessage("Boshiga qaytildi. Play tugmasini bosing.");
  }
  return { toggle, restart, message };
}
