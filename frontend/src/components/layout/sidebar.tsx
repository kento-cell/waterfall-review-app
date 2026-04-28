"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  disabled?: boolean;
  note?: string;
}

const navItems: NavItem[] = [
  { label: "プロジェクト一覧", href: "/projects" },
  { label: "観点マスタ", href: "/aspects", disabled: true, note: "Phase 6" },
  { label: "ナレッジ", href: "/knowledges", disabled: true, note: "Phase 6" },
  { label: "ユーザ管理", href: "/users", disabled: true, note: "Phase 7" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 border-r bg-muted/40 p-4">
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          if (item.disabled) {
            return (
              <span
                key={item.href}
                className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-muted-foreground"
                title={item.note}
              >
                <span>{item.label}</span>
                {item.note && <span className="text-xs">{item.note}</span>}
              </span>
            );
          }
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent",
                active && "bg-accent font-medium",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
