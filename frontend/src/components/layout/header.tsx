"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { authApi } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";

export function Header() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore: server-side logout best effort
    }
    logout();
    router.push("/login");
  };

  return (
    <header className="border-b bg-white">
      <div className="flex items-center justify-between px-6 py-3">
        <Link href="/projects" className="text-lg font-semibold">
          AIレビュー支援ツール
        </Link>
        <div className="flex items-center gap-3">
          {user && <span className="text-sm text-muted-foreground">{user.display_name}</span>}
          {user && (
            <Button variant="outline" size="sm" onClick={handleLogout}>
              ログアウト
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
