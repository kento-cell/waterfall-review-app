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

export default function LoginPage() {
  const router = useRouter();
  const { setToken, setUser } = useAuthStore();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

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
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4">
      <Card className="w-full max-w-md bg-white">
        <CardHeader>
          <CardTitle>ログイン</CardTitle>
          <CardDescription>AIレビュー支援ツール</CardDescription>
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
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
