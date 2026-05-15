"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Scale,
  MessageCircle,
  ShieldCheck,
  Clock,
  Sparkles,
  TrendingDown,
  Calendar,
  Bot,
  CheckCircle2,
  Phone,
  ArrowRight,
  Award,
  Heart,
  Lock,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const WHATSAPP_URL = "http://187.127.12.125:3001";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-md">
        <div className="container max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="size-9 rounded-lg bg-gradient-to-br from-brand to-brand-dark grid place-items-center text-white">
              <Scale className="size-5" />
            </div>
            <div>
              <div className="font-semibold">Andrade & Lemos</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Advogados</div>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm">
            <a href="#como-funciona" className="hover:text-primary transition">Como funciona</a>
            <a href="#beneficios" className="hover:text-primary transition">Benefícios</a>
            <a href="#faq" className="hover:text-primary transition">FAQ</a>
            <Link href="/login" className="text-xs text-muted-foreground hover:text-foreground">Admin</Link>
          </nav>
          <Button asChild size="sm" className="bg-brand hover:bg-brand-dark text-white">
            <a href={WHATSAPP_URL} target="_blank" rel="noreferrer">
              <MessageCircle className="size-4 mr-1.5" /> Falar agora
            </a>
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,hsl(var(--primary)/0.15),transparent_60%)]" />
        </div>
        <div className="container max-w-6xl mx-auto px-6 py-20 md:py-28 grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand/10 text-brand text-xs font-medium border border-brand/30">
              <Sparkles className="size-3" /> Atendimento jurídico 24/7 via WhatsApp
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight tracking-tight">
              Reajuste abusivo do plano de saúde?
              <br />
              <span className="bg-gradient-to-r from-brand to-brand-dark bg-clip-text text-transparent">
                Vamos analisar seu caso.
              </span>
            </h1>
            <p className="text-lg text-muted-foreground leading-relaxed">
              Escritório especializado em direito do consumidor com foco em planos de saúde.
              Fale agora pelo WhatsApp — Natasha, nossa assistente jurídica, vai te orientar
              e marcar uma análise com o Dr. Filipe.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button asChild size="lg" className="bg-brand hover:bg-brand-dark text-white h-12 px-6">
                <a href={WHATSAPP_URL} target="_blank" rel="noreferrer">
                  <MessageCircle className="size-5 mr-2" /> Iniciar conversa
                </a>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-12 px-6">
                <a href="#como-funciona">
                  Como funciona <ArrowRight className="size-4 ml-2" />
                </a>
              </Button>
            </div>
            <div className="flex flex-wrap items-center gap-6 pt-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="size-4 text-brand" /> OAB/AL ativo
              </div>
              <div className="flex items-center gap-1.5">
                <Clock className="size-4 text-brand" /> Resposta em minutos
              </div>
              <div className="flex items-center gap-1.5">
                <Lock className="size-4 text-brand" /> Dados protegidos
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:justify-self-end w-full max-w-md"
          >
            <div className="rounded-2xl border bg-card shadow-2xl overflow-hidden">
              <div className="bg-brand text-white px-4 py-3 flex items-center gap-3">
                <div className="size-10 rounded-full bg-white/20 grid place-items-center text-lg">
                  N
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-sm">Natasha · Andrade & Lemos</div>
                  <div className="text-[11px] opacity-80 flex items-center gap-1">
                    <span className="size-1.5 rounded-full bg-emerald-300 animate-pulse" /> online · responde agora
                  </div>
                </div>
              </div>
              <div className="whatsapp-bg-light dark:whatsapp-bg p-4 space-y-2 min-h-[360px]">
                <ChatBubble side="left" delay={0.5}>
                  Bom dia, Maria! Aqui é a Natasha, assistente do escritório.
                  Vi que você quer entender melhor esse reajuste do plano. Vou te
                  fazer 4 perguntas rápidas. Tudo bem?
                </ChatBubble>
                <ChatBubble side="right" delay={0.8}>
                  Sim, tudo bem 😊
                </ChatBubble>
                <ChatBubble side="left" delay={1.2}>
                  Quanto você está pagando atualmente de mensalidade?
                </ChatBubble>
                <ChatBubble side="right" delay={1.6}>
                  R$ 1.450
                </ChatBubble>
                <ChatBubble side="left" delay={2}>
                  Anotei. E qual é a operadora?
                </ChatBubble>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="container max-w-6xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat number="100%" label="Atendimento online" />
        <Stat number="30min" label="Consulta jurídica" />
        <Stat number="24/7" label="Disponível sempre" />
        <Stat number="BR" label="Atende todo o Brasil" />
      </section>

      <section id="como-funciona" className="bg-muted/30 border-y py-20">
        <div className="container max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">Em 3 passos simples</h2>
            <p className="text-muted-foreground mt-2">Da primeira mensagem à consulta marcada</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            <Step
              n="1"
              icon={MessageCircle}
              title="Inicie a conversa"
              desc="Clique no botão do WhatsApp. Natasha te atende e faz 4 perguntas rápidas sobre seu plano: valor, operadora, data de adesão e modalidade."
            />
            <Step
              n="2"
              icon={Calendar}
              title="Escolha um horário"
              desc="A IA consulta a agenda real do Dr. Filipe em tempo real e te sugere horários livres no chat. Você escolhe respondendo o número."
            />
            <Step
              n="3"
              icon={Award}
              title="Análise jurídica"
              desc="O Dr. Filipe te atende por WhatsApp ou videoconferência no horário marcado, analisa seu caso e te orienta sobre os próximos passos."
            />
          </div>
        </div>
      </section>

      <section id="beneficios" className="py-20">
        <div className="container max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">Por que escolher a gente</h2>
            <p className="text-muted-foreground mt-2">Tecnologia + advocacia especializada</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Feature
              icon={Bot}
              title="Atendimento por IA 24/7"
              desc="Natasha responde a qualquer hora, agenda na hora e nunca te deixa esperando."
            />
            <Feature
              icon={ShieldCheck}
              title="Especialistas em planos de saúde"
              desc="Foco em reajustes abusivos. Conhecemos as regras da ANS, jurisprudência e operadoras."
            />
            <Feature
              icon={TrendingDown}
              title="Análise de viabilidade"
              desc="Antes de qualquer compromisso, fazemos uma análise técnica criteriosa do seu caso."
            />
            <Feature
              icon={Clock}
              title="Sem espera, sem deslocamento"
              desc="100% online — consulta por WhatsApp ou videoconferência, quando for melhor pra você."
            />
            <Feature
              icon={Heart}
              title="Linguagem humana e clara"
              desc="Nada de juridiquês. Explicamos seu caso de um jeito que você entende."
            />
            <Feature
              icon={CheckCircle2}
              title="Transparência total"
              desc="Sem promessas vazias. Análise técnica, prudente e baseada em evidências."
            />
          </div>
        </div>
      </section>

      <section className="container max-w-6xl mx-auto px-6 py-16">
        <div className="rounded-3xl bg-gradient-to-br from-brand to-brand-dark text-white p-10 md:p-14 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-3">
            Seu plano subiu de forma absurda?
          </h2>
          <p className="text-white/90 text-lg mb-6 max-w-2xl mx-auto">
            Análise técnica sem compromisso. Em minutos você fala com nossa
            assistente jurídica e marca uma consulta com o Dr. Filipe.
          </p>
          <Button asChild size="lg" variant="secondary" className="h-12 px-6 bg-white text-brand-dark hover:bg-white/90">
            <a href={WHATSAPP_URL} target="_blank" rel="noreferrer">
              <MessageCircle className="size-5 mr-2" /> Falar com Natasha agora
            </a>
          </Button>
        </div>
      </section>

      <section id="faq" className="bg-muted/30 border-y py-20">
        <div className="container max-w-3xl mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-10">Perguntas frequentes</h2>
          <div className="space-y-3">
            <FAQ q="Onde fica o escritório?" a="Sede em Maceió, Alagoas. Mas atendemos clientes de todos os estados do Brasil — 100% online por WhatsApp ou videoconferência." />
            <FAQ q="A consulta tem custo?" a="Os valores e honorários o Dr. Filipe te explica pessoalmente na consulta, porque depende da análise do seu caso específico." />
            <FAQ q="Quanto tempo dura a consulta?" a="A consulta inicial dura cerca de 30 minutos, feita por WhatsApp ou videoconferência no horário que você escolher." />
            <FAQ q="Quais documentos preciso?" a="Para a consulta inicial, basta ter em mãos o boleto ou comunicado de reajuste do plano. Demais documentos serão pedidos se necessário." />
            <FAQ q="Vocês atendem em qualquer cidade?" a="Sim, atendemos todo o Brasil. Como o atendimento é 100% online, não há limitação geográfica." />
            <FAQ q="Quanto tempo demora pra ter resposta?" a="Natasha (IA) responde em segundos no WhatsApp. A consulta com o Dr. Filipe pode ser marcada normalmente para o mesmo dia ou nos próximos." />
          </div>
        </div>
      </section>

      <footer className="border-t py-10">
        <div className="container max-w-6xl mx-auto px-6 grid md:grid-cols-3 gap-8 text-sm">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="size-9 rounded-lg bg-gradient-to-br from-brand to-brand-dark grid place-items-center text-white">
                <Scale className="size-5" />
              </div>
              <span className="font-semibold">Andrade & Lemos Advogados</span>
            </div>
            <p className="text-muted-foreground text-xs leading-relaxed">
              Especializados em direito do consumidor e planos de saúde.
              Atendimento 100% online em todo o Brasil.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-3">Contato</h3>
            <ul className="space-y-1 text-muted-foreground text-xs">
              <li className="flex items-center gap-2"><MessageCircle className="size-3.5" /> WhatsApp via Natasha</li>
              <li className="flex items-center gap-2"><Phone className="size-3.5" /> Maceió, Alagoas — atendimento nacional</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-3">Importante</h3>
            <p className="text-muted-foreground text-[11px] leading-relaxed">
              As informações fornecidas pela Natasha são orientações iniciais e não substituem uma análise jurídica formal pelo advogado responsável.
            </p>
          </div>
        </div>
        <div className="container max-w-6xl mx-auto px-6 mt-8 text-center text-xs text-muted-foreground border-t pt-6">
          © {new Date().getFullYear()} Andrade & Lemos Advogados · OAB
        </div>
      </footer>
    </div>
  );
}

function Stat({ number, label }: { number: string; label: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="text-center"
    >
      <div className="text-3xl md:text-4xl font-bold bg-gradient-to-br from-brand to-brand-dark bg-clip-text text-transparent">
        {number}
      </div>
      <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">{label}</div>
    </motion.div>
  );
}

function Step({ n, icon: Icon, title, desc }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="rounded-2xl border bg-card p-6 hover:shadow-lg hover:-translate-y-0.5 transition"
    >
      <div className="size-12 rounded-xl bg-brand/10 text-brand grid place-items-center mb-4">
        <Icon className="size-6" />
      </div>
      <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Passo {n}</div>
      <h3 className="font-semibold text-lg mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
    </motion.div>
  );
}

function Feature({ icon: Icon, title, desc }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="rounded-xl border bg-card p-5 hover:border-brand/40 transition"
    >
      <div className="size-9 rounded-lg bg-brand/10 text-brand grid place-items-center mb-3">
        <Icon className="size-5" />
      </div>
      <h3 className="font-semibold mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
    </motion.div>
  );
}

function FAQ({ q, a }: { q: string; a: string }) {
  return (
    <details className="group rounded-lg border bg-card open:bg-accent/30">
      <summary className="cursor-pointer p-4 font-medium flex items-center justify-between">
        {q}
        <ArrowRight className="size-4 text-muted-foreground group-open:rotate-90 transition" />
      </summary>
      <div className="px-4 pb-4 text-sm text-muted-foreground leading-relaxed">{a}</div>
    </details>
  );
}

function ChatBubble({ side, children, delay }: { side: "left" | "right"; children: React.ReactNode; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className={side === "right" ? "flex justify-end" : "flex justify-start"}
    >
      <div
        className={
          side === "right"
            ? "max-w-[80%] bg-[#d9fdd3] dark:bg-emerald-900/40 text-zinc-900 dark:text-zinc-100 rounded-lg rounded-tr-none px-3 py-2 text-sm shadow-sm"
            : "max-w-[80%] bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-lg rounded-tl-none px-3 py-2 text-sm shadow-sm"
        }
      >
        {children}
      </div>
    </motion.div>
  );
}
