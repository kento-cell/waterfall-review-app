"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { authApi } from "@/lib/api/auth";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";

export default function AuthedLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, user, setUser, logout } = useAuthStore();
  const [hydrated, setHydrated] = React.useState(false);

  React.useEffect(() => {
    setHydrated(true);
  }, []);

  React.useEffect(() => {
    if (hydrated && !token) {
      router.replace("/login");
    }
  }, [hydrated, token, router]);

  // バックエンドからユーザ情報をリフレッシュ (トークン無効ならログイン画面)
  useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        const me = await authApi.me();
        setUser(me);
        return me;
      } catch (e) {
        logout();
        router.replace("/login");
        throw e;
      }
    },
    enabled: hydrated && !!token,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  if (!hydrated) return null;
  if (!token) return null;

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6">
          {user ? children : <div className="text-sm text-muted-foreground">読み込み中...</div>}
        </main>
      </div>
    </div>
  );
}
