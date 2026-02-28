"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Season } from "@/lib/types";
import { useState } from "react";

export default function Navbar({ seasons }: { seasons: Season[] }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link
          href="/"
          className="text-lg font-extrabold tracking-tight text-[var(--color-text)] no-underline"
        >
          Pick&apos;em
        </Link>

        <div className="flex items-center gap-4 text-sm font-semibold">
          {/* Season dropdown */}
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center gap-1 rounded-md px-3 py-1.5 transition hover:bg-[var(--color-surface2)]"
            >
              Seasons
              <span className="text-xs text-[var(--color-text-muted)]">▾</span>
            </button>
            {menuOpen && (
              <div className="absolute right-0 top-full mt-1 min-w-[140px] rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] py-1 shadow-lg">
                {seasons.map((s) => (
                  <Link
                    key={s.id}
                    href={`/seasons/${s.id}`}
                    onClick={() => setMenuOpen(false)}
                    className={`block px-4 py-2 text-sm no-underline transition hover:bg-[var(--color-surface2)] ${
                      pathname === `/seasons/${s.id}`
                        ? "font-bold text-[var(--color-accent)]"
                        : "text-[var(--color-text)]"
                    }`}
                  >
                    {s.label}
                  </Link>
                ))}
              </div>
            )}
          </div>

          <Link
            href="/players"
            className={`rounded-md px-3 py-1.5 no-underline transition hover:bg-[var(--color-surface2)] ${
              pathname.startsWith("/players")
                ? "text-[var(--color-accent)]"
                : "text-[var(--color-text)]"
            }`}
          >
            Players
          </Link>
        </div>
      </div>
    </nav>
  );
}
