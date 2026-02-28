"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import type { ChartPlayerData } from "@/lib/types";

interface Props {
  data: ChartPlayerData[];
  weeks: number[];
}

const BAR_H = 48;
const SPEEDS = [1500, 750, 375];
const SPEED_LABELS = ["1x", "2x", "4x"];
const CONFETTI_COLORS = [
  "#4a7c96", "#c0504d", "#3d8b5e", "#7b6b9e",
  "#c98442", "#5a9e9e", "#d4af37", "#96506e",
];

export default function AtsChartRace({ data, weeks }: Props) {
  const trackRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const barsRef = useRef<
    { el: HTMLDivElement; track: HTMLDivElement; fill: HTMLDivElement; valEl: HTMLSpanElement; idx: number }[]
  >([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentWeekRef = useRef(0);
  const speedIdxRef = useRef(0);
  const celebRef = useRef<HTMLDivElement>(null);
  const hasAutoPlayed = useRef(false);
  const [weekLabel, setWeekLabel] = useState(`Week ${weeks[0]} of ${weeks.length}`);
  const [playLabel, setPlayLabel] = useState("▶ Play");
  const [speedLabel, setSpeedLabel] = useState("1x");
  const initialized = useRef(false);

  // Compute symmetric scale
  const scaleRef = useRef({ atsMin: 0, atsMax: 0, atsRange: 1 });
  if (scaleRef.current.atsRange === 1) {
    let min = 0, max = 0;
    data.forEach((d) =>
      d.values.forEach((v) => {
        if (v < min) min = v;
        if (v > max) max = v;
      })
    );
    const absMax = Math.max(Math.abs(min), Math.abs(max), 5);
    const padded = Math.ceil(absMax / 5) * 5 + 5;
    scaleRef.current = { atsMin: -padded, atsMax: padded, atsRange: padded * 2 };
  }

  const zeroPct = useCallback(() => {
    const { atsMin, atsRange } = scaleRef.current;
    return ((0 - atsMin) / atsRange) * 100;
  }, []);

  const renderWeek = useCallback(
    (wi: number) => {
      const { atsMin, atsRange } = scaleRef.current;
      const zp = zeroPct();
      const snap = data.map((d, i) => ({ idx: i, val: d.values[wi] }));
      snap.sort((a, b) => b.val - a.val);
      const rank: Record<number, number> = {};
      snap.forEach((s, r) => { rank[s.idx] = r; });

      barsRef.current.forEach((b) => {
        const v = data[b.idx].values[wi];
        const valPct = ((v - atsMin) / atsRange) * 100;

        if (v >= 0) {
          b.fill.style.left = `${zp}%`;
          b.fill.style.width = `${valPct - zp}%`;
        } else {
          b.fill.style.left = `${valPct}%`;
          b.fill.style.width = `${zp - valPct}%`;
        }

        b.valEl.textContent = v >= 0 ? `+${v.toFixed(1)}` : v.toFixed(1);
        b.valEl.style.left = v >= 0 ? `${valPct + 1}%` : "auto";
        b.valEl.style.right = v < 0 ? `${100 - valPct + 1}%` : "auto";
        b.el.style.top = `${rank[b.idx] * BAR_H}px`;
      });
      setWeekLabel(`Week ${weeks[wi]} of ${weeks.length}`);
    },
    [data, weeks, zeroPct]
  );

  const clearCelebration = useCallback(() => {
    if (celebRef.current) {
      celebRef.current.style.display = "none";
      celebRef.current.innerHTML = "";
    }
    containerRef.current
      ?.querySelectorAll(".confetti-piece")
      .forEach((p) => p.remove());
  }, []);

  const celebrate = useCallback(() => {
    let winnerIdx = 0;
    let winnerVal = -Infinity;
    data.forEach((d, i) => {
      const v = d.values[d.values.length - 1];
      if (v > winnerVal) { winnerVal = v; winnerIdx = i; }
    });
    const winner = data[winnerIdx];

    if (celebRef.current) {
      const avatarHtml = winner.avatarUrl
        ? `<img class="winner-avatar" src="${winner.avatarUrl}" alt="${winner.name}">`
        : `<span class="winner-avatar" style="background:${winner.color};display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.5rem;font-weight:800">${winner.name[0]}</span>`;

      celebRef.current.innerHTML = `
        <div class="winner-banner">
          ${avatarHtml}
          <div class="winner-name">${winner.name} wins!</div>
          <div class="winner-value">${winnerVal >= 0 ? "+" : ""}${winnerVal.toFixed(1)} ATS</div>
        </div>`;
      celebRef.current.style.display = "flex";
    }

    if (containerRef.current) {
      for (let i = 0; i < 60; i++) {
        const piece = document.createElement("div");
        piece.className = "confetti-piece";
        piece.style.background = CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)];
        piece.style.left = `${10 + Math.random() * 80}%`;
        piece.style.top = `${Math.random() * 30}%`;
        piece.style.width = `${6 + Math.random() * 6}px`;
        piece.style.height = `${6 + Math.random() * 6}px`;
        piece.style.borderRadius = Math.random() > 0.5 ? "50%" : "2px";
        piece.style.animation = `confettiFall ${1.2 + Math.random() * 1.5}s ease-out ${Math.random() * 0.5}s forwards`;
        containerRef.current.appendChild(piece);
      }
    }
  }, [data]);

  const stopAnim = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (currentWeekRef.current < weeks.length - 1) setPlayLabel("▶ Play");
  }, [weeks.length]);

  const advance = useCallback(() => {
    if (currentWeekRef.current >= weeks.length - 1) {
      stopAnim();
      setPlayLabel("▶ Replay");
      celebrate();
      return;
    }
    currentWeekRef.current++;
    renderWeek(currentWeekRef.current);
  }, [weeks.length, stopAnim, celebrate, renderWeek]);

  const playAnim = useCallback(() => {
    if (currentWeekRef.current >= weeks.length - 1) {
      currentWeekRef.current = 0;
      clearCelebration();
      barsRef.current.forEach((b) => {
        b.el.style.transition = "none";
        b.fill.style.transition = "none";
      });
      renderWeek(0);
      trackRef.current?.offsetHeight;
      barsRef.current.forEach((b) => {
        b.el.style.transition = "";
        b.fill.style.transition = "";
      });
    }
    clearCelebration();
    intervalRef.current = setInterval(advance, SPEEDS[speedIdxRef.current]);
    setPlayLabel("⏸ Pause");
  }, [weeks.length, advance, clearCelebration, renderWeek]);

  const resetAnim = useCallback(() => {
    stopAnim();
    currentWeekRef.current = 0;
    clearCelebration();
    barsRef.current.forEach((b) => {
      b.el.style.transition = "none";
      b.fill.style.transition = "none";
    });
    renderWeek(0);
    trackRef.current?.offsetHeight;
    barsRef.current.forEach((b) => {
      b.el.style.transition = "";
      b.fill.style.transition = "";
    });
    setPlayLabel("▶ Play");
  }, [stopAnim, clearCelebration, renderWeek]);

  useEffect(() => {
    if (initialized.current || !trackRef.current) return;
    initialized.current = true;

    const track = trackRef.current;
    track.innerHTML = "";
    barsRef.current = [];

    data.forEach((d, i) => {
      const row = document.createElement("div");
      row.className = "race-bar";
      row.style.top = `${i * BAR_H}px`;

      const avatarTag = d.avatarUrl
        ? `<img class="race-bar-avatar" src="${d.avatarUrl}" alt="${d.name}">`
        : `<span class="race-bar-avatar-placeholder" style="background:${d.color}">${d.name[0]}</span>`;

      const trackEl = document.createElement("div");
      row.innerHTML = `<span class="race-bar-name">${avatarTag}<span class="race-bar-label">${d.name}</span></span>`;

      const atsTrack = document.createElement("div");
      atsTrack.className = "ats-bar-track";

      const zeroLine = document.createElement("div");
      zeroLine.className = "ats-zero-line";
      zeroLine.style.left = `${zeroPct()}%`;
      atsTrack.appendChild(zeroLine);

      const fill = document.createElement("div");
      fill.className = "ats-bar-fill";
      fill.style.background = d.color;
      atsTrack.appendChild(fill);

      const valEl = document.createElement("span");
      valEl.className = "ats-bar-value";
      valEl.textContent = "0.0";
      atsTrack.appendChild(valEl);

      row.appendChild(atsTrack);
      track.appendChild(row);

      barsRef.current.push({ el: row, track: atsTrack, fill, valEl, idx: i });
    });

    track.style.height = `${data.length * BAR_H}px`;
    renderWeek(0);

    const section = containerRef.current;
    if (section && !hasAutoPlayed.current) {
      const obs = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && !intervalRef.current && currentWeekRef.current === 0) {
            hasAutoPlayed.current = true;
            playAnim();
            obs.disconnect();
          }
        },
        { threshold: 0.3 }
      );
      obs.observe(section);
      return () => obs.disconnect();
    }
  }, [data, renderWeek, playAnim, zeroPct]);

  return (
    <section className="card" ref={containerRef} style={{ position: "relative" }}>
      <h2 className="mb-3 text-lg font-bold">ATS Bonus Race</h2>
      <div className="chart-controls">
        <span className="week-label">{weekLabel}</span>
        <div className="flex gap-2">
          <button
            className="ctrl-btn"
            onClick={() => {
              if (intervalRef.current) stopAnim();
              else playAnim();
            }}
            dangerouslySetInnerHTML={{ __html: playLabel }}
          />
          <button className="ctrl-btn" onClick={resetAnim}>
            ↺ Reset
          </button>
          <button
            className="ctrl-btn"
            onClick={() => {
              speedIdxRef.current = (speedIdxRef.current + 1) % SPEEDS.length;
              setSpeedLabel(SPEED_LABELS[speedIdxRef.current]);
              if (intervalRef.current) {
                stopAnim();
                playAnim();
              }
            }}
          >
            {speedLabel}
          </button>
        </div>
      </div>
      <div ref={trackRef} className="race-track" />
      <div
        ref={celebRef}
        className="celebration-overlay"
        style={{ display: "none" }}
      />
    </section>
  );
}
