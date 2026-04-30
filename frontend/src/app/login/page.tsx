"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuthStore } from "@/store/auth";
import { authApi } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const loginSchema = z.object({
  email: z.string().email("メールアドレスの形式が不正です"),
  password: z.string().min(1, "パスワードは必須です"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

const DEMO_CREDENTIALS: LoginFormValues = {
  email: "demo@example.com",
  password: "password123",
};

export default function LoginPage() {
  const router = useRouter();
  const { setToken, setUser } = useAuthStore();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const fillDemoCredentials = () => {
    setServerError(null);
    setValue("email", DEMO_CREDENTIALS.email, { shouldValidate: true });
    setValue("password", DEMO_CREDENTIALS.password, { shouldValidate: true });
  };

  const onSubmit = async (values: LoginFormValues) => {
    setServerError(null);
    try {
      const { access_token } = await authApi.login(values);
      setToken(access_token);
      const me = await authApi.me();
      setUser(me);
      router.push("/projects");
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "ログインに失敗しました";
      setServerError(typeof detail === "string" ? detail : "ログインに失敗しました");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top_left,_#e0f2fe,_transparent_34%),linear-gradient(135deg,_#f8fafc_0%,_#eef2ff_100%)] px-4">
      <Card className="w-full max-w-md border-slate-200 bg-white/95 shadow-xl">
        <CardHeader>
          <div className="mb-2 inline-flex w-fit rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
            Waterfall Review
          </div>
          <CardTitle>ログイン</CardTitle>
          <CardDescription>AIレビュー支援ツールにアクセスします</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="email">メールアドレス</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                {...register("email")}
                aria-invalid={!!errors.email}
              />
              {errors.email && <span className="text-xs text-destructive">{errors.email.message}</span>}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">パスワード</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                {...register("password")}
                aria-invalid={!!errors.password}
              />
              {errors.password && <span className="text-xs text-destructive">{errors.password.message}</span>}
            </div>
            {serverError && <span className="text-sm text-destructive">{serverError}</span>}
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "ログイン中..." : "ログイン"}
            </Button>
            <div className="rounded-lg border border-dashed bg-slate-50 p-3 text-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-medium">デモアカウント</p>
                  <p className="text-xs text-muted-foreground">demo@example.com / password123</p>
                </div>
                <Button type="button" variant="outline" size="sm" onClick={fillDemoCredentials}>
                  入力する
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
