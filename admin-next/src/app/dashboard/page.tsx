"use client";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Users,
  CalendarCheck,
  Hourglass,
  UserCog,
  TrendingUp,
  WifiOff,
  Wifi,
  Activity,
  Sparkles,
} from "lucide-react";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  CartesianGrid,
  Legend,
} from "recharts";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge, Skeleton } from "@/components/ui/index";
import { PageHeader } from "@/components/page-header";

const COLORS = ["#25D366", "#34E07A", "#128C7E", "#0a8068", "#D4AF37", "#8E44AD", "#3498DB", "#E67E22"];

export default function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboardStats });

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Visão geral do bot e dos atendimentos em tempo real"
        action={
          <div className="flex items-center gap-2">
            {data?.wa_status === "connected" ? (
              <Badge variant="success" className="gap-1.5">
                <Wifi className="size-3" /> WhatsApp conectado
              </Badge>
            ) : data?.wa_status === "waiting" ? (
              <Badge variant="warning" className="gap-1.5">
                <Hourglass className="size-3" /> Aguardando QR
              </Badge>
            ) : (
              <Badge variant="danger" className="gap-1.5">
                <WifiOff className="size-3" /> {data?.wa_status || "offline"}
              </Badge>
            )}
            {data?.api_status === "ok" && (
              <Badge variant="info" className="gap-1.5">
                <Activity className="size-3" /> API saudável
              </Badge>
            )}
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* KPI cards */}
        <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
          <StatCard
            label="Total de leads"
            value={data?.total_leads}
            icon={Users}
            color="text-blue-400"
            loading={isLoading}
            delay={0}
          />
          <StatCard
            label="Agendados"
            value={data?.agendados}
            icon={CalendarCheck}
            color="text-emerald-400"
            loading={isLoading}
            delay={0.05}
          />
          <StatCard
            label="Qualificando"
            value={data?.qualificando}
            icon={Hourglass}
            color="text-amber-400"
            loading={isLoading}
            delay={0.1}
          />
          <StatCard
            label="Handoff humano"
            value={data?.handoff}
            icon={UserCog}
            color="text-rose-400"
            loading={isLoading}
            delay={0.15}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          {/* Leads timeline */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="size-4 text-primary" /> Leads — últimos 30 dias
              </CardTitle>
              <CardDescription>Novos atendimentos por dia</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              {isLoading ? (
                <Skeleton className="h-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data?.leads_por_dia || []}>
                    <defs>
                      <linearGradient id="gradGreen" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#25D366" stopOpacity={0.6} />
                        <stop offset="95%" stopColor="#25D366" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                    <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--popover))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="count"
                      stroke="#25D366"
                      strokeWidth={2}
                      fill="url(#gradGreen)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Funnel */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Funil de conversão</CardTitle>
              <CardDescription>Por etapa do atendimento</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              {isLoading ? (
                <Skeleton className="h-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data?.funil || []} layout="vertical" margin={{ left: 30 }}>
                    <XAxis type="number" hide />
                    <YAxis dataKey="etapa" type="category" width={100} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--popover))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Bar dataKey="count" fill="#25D366" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Cenários — diagnóstico Natasha */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="size-4 text-primary" /> Diagnóstico por cenário
            </CardTitle>
            <CardDescription>
              Como a Natasha está classificando os casos (Falso Coletivo, Multifamiliar, etc.)
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            {isLoading ? (
              <Skeleton className="h-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.por_cenario || []} layout="vertical" margin={{ left: 80 }}>
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" width={140} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--popover))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                    {(data?.por_cenario || []).map((c, i) => (
                      <Cell
                        key={i}
                        fill={
                          c.name === "Falso Coletivo" ? "#25D366"
                          : c.name === "Multifamiliar" ? "#3498DB"
                          : c.name === "Coletivo Adesão" ? "#D4AF37"
                          : c.name === "Individual/Familiar" ? "#8E44AD"
                          : c.name === "Inviável" ? "#E74C3C"
                          : "#7F8C8D"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Distribuições */}
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Por operadora</CardTitle>
              <CardDescription>Distribuição dos leads</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              {isLoading ? (
                <Skeleton className="h-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data?.por_operadora || []}
                      dataKey="value"
                      nameKey="name"
                      outerRadius={80}
                      innerRadius={40}
                      strokeWidth={2}
                      stroke="hsl(var(--background))"
                    >
                      {(data?.por_operadora || []).map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--popover))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Por modalidade do plano</CardTitle>
              <CardDescription>Tipo de contrato dos leads</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              {isLoading ? (
                <Skeleton className="h-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data?.por_modalidade || []}
                      dataKey="value"
                      nameKey="name"
                      outerRadius={80}
                      innerRadius={40}
                      strokeWidth={2}
                      stroke="hsl(var(--background))"
                    >
                      {(data?.por_modalidade || []).map((_, i) => (
                        <Cell key={i} fill={COLORS[(i + 2) % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--popover))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Próximas consultas */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Próximas consultas (7 dias)</CardTitle>
            <CardDescription>Compromissos agendados na agenda do Dr. Filipe</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-10" />
                <Skeleton className="h-10" />
                <Skeleton className="h-10" />
              </div>
            ) : (data?.upcoming_consultas || []).length === 0 ? (
              <div className="text-sm text-muted-foreground py-8 text-center">
                Nenhuma consulta nos próximos 7 dias.
              </div>
            ) : (
              <div className="space-y-2">
                {(data?.upcoming_consultas || []).map((c, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="flex items-center justify-between p-3 rounded-lg border bg-card/50 hover:bg-accent/50 transition"
                  >
                    <div className="flex items-center gap-3">
                      <div className="size-9 rounded-md bg-primary/10 grid place-items-center text-primary">
                        <CalendarCheck className="size-4" />
                      </div>
                      <div>
                        <div className="text-sm font-medium">{c.titulo}</div>
                        <div className="text-xs text-muted-foreground">{c.inicio}</div>
                      </div>
                    </div>
                    {c.criado_pelo_bot ? (
                      <Badge variant="success" className="text-[10px]">🤖 Bot</Badge>
                    ) : (
                      <Badge variant="secondary" className="text-[10px]">manual</Badge>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  loading,
  delay,
}: {
  label: string;
  value?: number;
  icon: any;
  color: string;
  loading: boolean;
  delay: number;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.3 }}>
      <Card className="overflow-hidden">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-xs text-muted-foreground uppercase tracking-wide">{label}</div>
              {loading ? (
                <Skeleton className="h-8 w-16 mt-2" />
              ) : (
                <div className="text-3xl font-bold mt-1 tabular-nums">{value ?? 0}</div>
              )}
            </div>
            <div className={`size-9 rounded-lg bg-muted grid place-items-center ${color}`}>
              <Icon className="size-4" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
