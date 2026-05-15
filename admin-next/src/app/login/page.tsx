"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Scale, LogIn } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/index";

export default function LoginPage() {
  const router = useRouter();
  const [user, setUser] = useState("dheiver");
  const [pass, setPass] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const creds = btoa(`${user}:${pass}`);
      const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`, {
        headers: { Authorization: "Basic " + creds },
      });
      if (!r.ok) throw new Error("Credenciais inválidas");
      sessionStorage.setItem("admin_creds", creds);
      toast.success("Bem-vindo!");
      router.push("/dashboard");
    } catch (e: any) {
      toast.error("Falha no login", { description: String(e?.message || e) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 grid place-items-center bg-gradient-to-br from-background to-muted">
      <Card className="w-full max-w-sm border-primary/30">
        <CardContent className="p-8 space-y-6">
          <div className="text-center space-y-2">
            <div className="size-14 mx-auto rounded-xl bg-gradient-to-br from-brand to-brand-dark grid place-items-center text-primary-foreground">
              <Scale className="size-7" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Andrade & Lemos</h1>
              <p className="text-xs text-muted-foreground">Painel administrativo · Bot Natasha</p>
            </div>
          </div>

          <form onSubmit={submit} className="space-y-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Usuário</label>
              <Input value={user} onChange={(e) => setUser(e.target.value)} autoFocus />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Senha</label>
              <Input type="password" value={pass} onChange={(e) => setPass(e.target.value)} />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              <LogIn className="size-4 mr-2" /> {loading ? "Entrando..." : "Entrar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
