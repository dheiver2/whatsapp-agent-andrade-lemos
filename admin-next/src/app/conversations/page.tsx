"use client";
import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Search, MessageCircle, CheckCircle2, Clock, UserCog, Phone } from "lucide-react";
import { api, ConversationSummary } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, Input, Skeleton } from "@/components/ui/index";
import { cn } from "@/lib/utils";

const STAGES = ["todos", "abordagem_inicial", "qualificacao", "oferta_consulta", "agendamento", "confirmacao_consulta"];

function statusBadge(status: string) {
  const map: Record<string, { variant: any; icon: any; label: string }> = {
    scheduled: { variant: "success", icon: CheckCircle2, label: "agendado" },
    won: { variant: "success", icon: CheckCircle2, label: "ganho" },
    waiting_human: { variant: "warning", icon: UserCog, label: "humano" },
    ai_active: { variant: "info", icon: Clock, label: "ativa" },
    outbound_pending: { variant: "info", icon: Clock, label: "outbound" },
  };
  const m = map[status] || { variant: "secondary", icon: Clock, label: status };
  const Icon = m.icon;
  return (
    <Badge variant={m.variant} className="gap-1">
      <Icon className="size-3" /> {m.label}
    </Badge>
  );
}

export default function ConversationsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["conversations"], queryFn: api.conversations });
  const [search, setSearch] = useState("");
  const [stage, setStage] = useState("todos");

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.filter((p) => {
      if (stage !== "todos" && p.stage !== stage) return false;
      if (!search) return true;
      const s = search.toLowerCase();
      return (
        p.name?.toLowerCase().includes(s) ||
        p.phone?.toLowerCase().includes(s) ||
        p.operadora?.toLowerCase().includes(s)
      );
    });
  }, [data, search, stage]);

  return (
    <>
      <PageHeader
        title="Conversas"
        description={`${data?.length ?? 0} leads no total · ${filtered.length} filtrados`}
        action={
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="size-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Buscar nome, telefone, operadora…"
                className="pl-9 w-72"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        }
      />

      <div className="p-6 space-y-4">
        {/* Stage tabs */}
        <div className="flex flex-wrap gap-2">
          {STAGES.map((s) => (
            <button
              key={s}
              onClick={() => setStage(s)}
              className={cn(
                "px-3 py-1.5 rounded-md text-xs transition",
                stage === s
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-accent"
              )}
            >
              {s === "todos" ? "Todos" : s.replace(/_/g, " ")}
            </button>
          ))}
        </div>

        {/* List */}
        {isLoading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <MessageCircle className="size-12 mx-auto opacity-40 mb-3" />
              {data?.length === 0 ? "Nenhuma conversa ainda. Aguardando primeiro lead." : "Nenhum lead com esses filtros."}
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-2">
            {filtered.map((p, i) => (
              <ConvCard key={p.phone} p={p} index={i} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}

function ConvCard({ p, index }: { p: ConversationSummary; index: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.02 }}>
      <Link href={`/conversations/${encodeURIComponent(p.phone)}`}>
        <Card className="hover:bg-accent/30 transition cursor-pointer group">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="size-10 rounded-full bg-gradient-to-br from-brand to-brand-dark grid place-items-center text-primary-foreground font-semibold text-sm shrink-0">
              {(p.name?.[0] || "?").toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 flex-wrap">
                <div className="font-medium truncate">{p.name || "Sem nome"}</div>
                <div className="text-xs text-muted-foreground flex items-center gap-1">
                  <Phone className="size-3" /> {p.phone}
                </div>
              </div>
              <div className="text-xs text-muted-foreground flex items-center gap-3 flex-wrap mt-1">
                {p.operadora && p.operadora !== "?" && <span>📋 {p.operadora}</span>}
                {p.valor_atual && p.valor_atual !== "?" && <span>💰 R$ {p.valor_atual}</span>}
                {p.tipo_plano && p.tipo_plano !== "?" && <span>📑 {p.tipo_plano}</span>}
                {p.confirmed_slot_str && <span className="text-emerald-500">📅 {p.confirmed_slot_str}</span>}
              </div>
            </div>
            <div className="hidden md:flex items-center gap-2 shrink-0">
              <Badge variant="secondary" className="text-[10px]">{p.stage}</Badge>
              {statusBadge(p.lead_status)}
            </div>
          </CardContent>
        </Card>
      </Link>
    </motion.div>
  );
}
