"use client";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Pause, Play, RotateCcw, QrCode,
  CheckCircle2, AlertTriangle, ShieldAlert, Wifi, WifiOff,
  Hourglass, XCircle,
} from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/index";
import { ConfirmDialog } from "@/components/confirm-dialog";

const API = process.env.NEXT_PUBLIC_API_URL || "http://187.127.12.125:8001";

function authHeader() {
  const c = typeof window !== "undefined" ? sessionStorage.getItem("admin_creds") : null;
  return c ? { Authorization: "Basic " + c } : {};
}

async function call(path: string, init?: RequestInit) {
  const r = await fetch(API + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeader(), ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
  return r.json();
}

type BotState = "active" | "waiting_qr" | "paused" | "error" | "missing";
interface StatusResponse {
  containers: Record<string, { status: string; pid: number }>;
  bot_state: BotState;
  bot_state_label: string;
  wa_app_status: string | null;
}

const STATE_META: Record<BotState, { color: string; bg: string; border: string; icon: any; label: string }> = {
  active: { color: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/30", icon: CheckCircle2, label: "Ativo" },
  waiting_qr: { color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/30", icon: Hourglass, label: "Aguardando QR" },
  paused: { color: "text-slate-500", bg: "bg-slate-500/10", border: "border-slate-500/30", icon: Pause, label: "Pausado" },
  error: { color: "text-rose-500", bg: "bg-rose-500/10", border: "border-rose-500/30", icon: AlertTriangle, label: "Com erro" },
  missing: { color: "text-rose-500", bg: "bg-rose-500/10", border: "border-rose-500/30", icon: XCircle, label: "Inexistente" },
};

export default function ControlPage() {
  const qc = useQueryClient();
  const [confirm, setConfirm] = useState<null | "pause" | "resume" | "reset">(null);

  const { data, isLoading } = useQuery<StatusResponse>({
    queryKey: ["control-status"],
    queryFn: () => call("/api/admin/control/status"),
    refetchInterval: 4_000,
  });

  const state = data?.bot_state ?? "missing";
  const meta = STATE_META[state];
  const StateIcon = meta?.icon ?? AlertTriangle;

  const mutation = useMutation({
    mutationFn: (action: "pause" | "resume" | "reset") => call(`/api/admin/control/${action}`, { method: "POST" }),
    onSuccess: (resp, action) => {
      const action_label = action === "pause" ? "Bot pausado" : action === "resume" ? "Bot retomado" : "Sessão resetada";
      toast.success(action_label, { description: resp?.msg || "" });
      qc.invalidateQueries({ queryKey: ["control-status"] });
      setConfirm(null);
    },
    onError: (e: any) => {
      toast.error("Erro na ação", { description: String(e?.message || e) });
      setConfirm(null);
    },
  });

  const dialogTexts = {
    pause: {
      title: "Pausar atendimento?",
      desc: "O bot vai parar de receber mensagens. A sessão WhatsApp continua salva — você pode retomar a qualquer momento sem escanear de novo.",
    },
    resume: {
      title: "Retomar atendimento?",
      desc: state === "paused"
        ? "Religa o bot. A conexão WhatsApp é restaurada automaticamente do volume de sessão."
        : "Religa o bot.",
    },
    reset: {
      title: "Trocar número (resetar sessão)?",
      desc: "Esta ação apaga a sessão atual e gera um novo QR Code. O número atualmente conectado será DESVINCULADO. Você precisará escanear o novo QR — por isso só faça se realmente quiser trocar de número.",
    },
  };

  // Botões habilitados de acordo com estado real
  const canPause = state === "active" || state === "waiting_qr";
  const canResume = state === "paused" || state === "missing";
  const canReset = state !== "missing"; // reset sempre menos quando totalmente missing (cria de novo via compose)
  const needsScan = state === "waiting_qr";
  const isLoadingMutation = mutation.isPending;

  return (
    <>
      <PageHeader
        title="Controle"
        description="Tudo por clique — sem precisar SSH"
        action={
          <Badge variant="secondary" className={`gap-1.5 ${meta?.color || ""}`}>
            <StateIcon className="size-3" />
            {data?.bot_state_label || (isLoading ? "Verificando…" : "?")}
          </Badge>
        }
      />

      <div className="p-6 space-y-5">
        {/* Card de status grande — claro e descritivo */}
        <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>
          <Card className={`border-2 ${meta?.border}`}>
            <CardContent className="p-6 flex items-center gap-5">
              <div className={`size-14 rounded-2xl ${meta?.bg} ${meta?.color} grid place-items-center`}>
                <StateIcon className="size-7" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Estado do bot</div>
                <h2 className="text-2xl font-bold">{data?.bot_state_label || "Verificando…"}</h2>
                <div className="text-sm text-muted-foreground mt-1">
                  {state === "active" && "Está recebendo e respondendo mensagens em tempo real."}
                  {state === "waiting_qr" && (
                    <>
                      O container está rodando mas{" "}
                      <span className="text-amber-500 font-medium">ainda não há número vinculado.</span>{" "}
                      Acesse o QR e escaneie pelo WhatsApp do número que vai ser o bot.
                    </>
                  )}
                  {state === "paused" && "Bot pausado. Mensagens recebidas nesse período NÃO serão respondidas."}
                  {state === "error" && "Algo está errado. Olhe os logs ou faça reset da sessão."}
                  {state === "missing" && "Container não existe. Use 'Retomar' para criar."}
                </div>
              </div>
              {needsScan && (
                <Link href="/qr">
                  <Button size="lg" className="bg-amber-500 hover:bg-amber-600 text-white">
                    <QrCode className="size-5 mr-2" /> Abrir QR
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Botões de ação contextualizados */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <ActionCard
            icon={Pause}
            color="amber"
            label="Pausar atendimento"
            desc="Para o bot de receber mensagens"
            available={canPause}
            disabledMsg={state === "paused" ? "Bot já está pausado" : state === "missing" ? "Container não existe" : ""}
            loading={isLoadingMutation && mutation.variables === "pause"}
            onClick={() => setConfirm("pause")}
          />
          <ActionCard
            icon={Play}
            color="emerald"
            label={state === "missing" ? "Criar e ligar bot" : "Retomar atendimento"}
            desc="Religa o bot (restaura sessão se houver)"
            available={canResume}
            disabledMsg={!canResume ? "Bot já está ativo" : ""}
            loading={isLoadingMutation && mutation.variables === "resume"}
            onClick={() => setConfirm("resume")}
          />
          <ActionCard
            icon={RotateCcw}
            color="rose"
            label="Trocar número (resetar)"
            desc="Apaga sessão e gera novo QR"
            available={canReset}
            disabledMsg=""
            loading={isLoadingMutation && mutation.variables === "reset"}
            onClick={() => setConfirm("reset")}
            destructive
          />
        </div>

        {/* Containers detalhe (info técnica) */}
        <Card>
          <CardContent className="p-5">
            <h3 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wider">
              Containers (detalhe técnico)
            </h3>
            <div className="grid sm:grid-cols-3 gap-3">
              {Object.entries(data?.containers || {}).map(([name, c]) => {
                const ok = c.status === "running";
                return (
                  <div key={name} className="p-3 rounded-lg border bg-card/50">
                    <div className="text-[10px] text-muted-foreground font-mono truncate">{name}</div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-sm font-medium capitalize flex items-center gap-1.5">
                        {ok ? <Wifi className="size-3 text-emerald-500" /> : <WifiOff className="size-3 text-rose-500" />}
                        {c.status}
                      </span>
                      {ok && <span className="text-[10px] text-muted-foreground font-mono">pid {c.pid}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <p className="text-xs text-muted-foreground flex items-center gap-1.5">
          <ShieldAlert className="size-3" />
          Status atualiza a cada 4 segundos. As ações executam direto no Docker do host.
        </p>
      </div>

      <ConfirmDialog
        open={!!confirm}
        onClose={() => setConfirm(null)}
        title={confirm ? dialogTexts[confirm].title : ""}
        description={confirm ? dialogTexts[confirm].desc : ""}
        destructive={confirm === "reset"}
        loading={isLoadingMutation}
        onConfirm={() => confirm && mutation.mutate(confirm)}
      />
    </>
  );
}

function ActionCard({
  icon: Icon,
  color,
  label,
  desc,
  available,
  disabledMsg,
  loading,
  onClick,
  destructive,
}: {
  icon: any;
  color: "amber" | "emerald" | "rose";
  label: string;
  desc: string;
  available: boolean;
  disabledMsg: string;
  loading?: boolean;
  onClick: () => void;
  destructive?: boolean;
}) {
  const colors = {
    amber: { bg: "bg-amber-500/10", text: "text-amber-500", btn: "bg-amber-500 hover:bg-amber-600 text-white" },
    emerald: { bg: "bg-emerald-500/10", text: "text-emerald-500", btn: "bg-emerald-500 hover:bg-emerald-600 text-white" },
    rose: { bg: "bg-rose-500/10", text: "text-rose-500", btn: "bg-rose-500 hover:bg-rose-600 text-white" },
  };
  const c = colors[color];
  return (
    <Card className={`transition ${!available ? "opacity-50" : "hover:shadow-md hover:-translate-y-0.5"}`}>
      <CardContent className="p-5 flex flex-col h-full">
        <div className="flex items-start gap-3 mb-3">
          <div className={`size-10 rounded-lg ${c.bg} ${c.text} grid place-items-center shrink-0`}>
            <Icon className="size-5" />
          </div>
          <div>
            <h3 className="font-semibold">{label}</h3>
            <p className="text-xs text-muted-foreground">{desc}</p>
          </div>
        </div>
        <Button
          className={`w-full mt-auto ${available ? c.btn : ""}`}
          variant={!available ? "outline" : "default"}
          disabled={!available || loading}
          onClick={onClick}
        >
          {loading ? "Executando…" : !available && disabledMsg ? disabledMsg : label}
        </Button>
      </CardContent>
    </Card>
  );
}
