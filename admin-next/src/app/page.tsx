"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Scale, MessageCircle, ShieldCheck, Clock, Sparkles, TrendingDown,
  Calendar, Bot, CheckCircle2, Phone, ArrowRight, Award, Heart, Lock,
  Mic, Camera, FileSearch, Banknote, Users, Star, Quote,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const WHATSAPP_URL = "http://187.127.12.125:3001";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-md">
        <div className="container max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="size-9 rounded-lg bg-gradient-to-br from-brand to-brand-dark grid place-items-center text-white">
              <Scale className="size-5" />
            </div>
            <div>
              <div className="font-semibold">Andrade & Lemos</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider">Advogados · OAB/AL</div>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm">
            <a href="#como-funciona" className="hover:text-primary transition">Como funciona</a>
            <a href="#cenarios" className="hover:text-primary transition">Cenários</a>
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

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,hsl(var(--primary)/0.18),transparent_60%)]" />
        </div>
        <div className="container max-w-6xl mx-auto px-6 py-20 md:py-24 grid lg:grid-cols-2 gap-12 items-center">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand/10 text-brand text-xs font-medium border border-brand/30">
              <Sparkles className="size-3" /> Especialistas em planos de saúde · Atendimento 24/7
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-[1.05] tracking-tight">
              Reajuste abusivo do plano de saúde?
              <br />
              <span className="bg-gradient-to-r from-brand to-brand-dark bg-clip-text text-transparent">
                Pode reduzir até 50% e recuperar até 3 anos.
              </span>
            </h1>
            <p className="text-lg text-muted-foreground leading-relaxed">
              Muitos planos &quot;coletivos empresariais&quot; vendidos para famílias são, na prática, <strong className="text-foreground">falsos coletivos</strong> — e a Justiça vem reconhecendo isso.
              Fale com a <strong className="text-foreground">Natasha</strong>, nossa assistente jurídica, pelo WhatsApp. Em 5 perguntas ela analisa seu caso e marca uma consulta com o <strong className="text-foreground">Dr. Filipe Lima</strong>.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button asChild size="lg" className="bg-brand hover:bg-brand-dark text-white h-12 px-6">
                <a href={WHATSAPP_URL} target="_blank" rel="noreferrer">
                  <MessageCircle className="size-5 mr-2" /> Iniciar conversa no WhatsApp
                </a>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-12 px-6">
                <a href="#como-funciona">Como funciona <ArrowRight className="size-4 ml-2" /></a>
              </Button>
            </div>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 pt-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1.5"><ShieldCheck className="size-4 text-brand" /> OAB/AL ativo</div>
              <div className="flex items-center gap-1.5"><Clock className="size-4 text-brand" /> Resposta em segundos</div>
              <div className="flex items-center gap-1.5"><Lock className="size-4 text-brand" /> LGPD · dados protegidos</div>
              <div className="flex items-center gap-1.5"><Award className="size-4 text-brand" /> Atendimento nacional</div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6, delay: 0.2 }} className="lg:justify-self-end w-full max-w-md">
            <div className="rounded-2xl border bg-card shadow-2xl overflow-hidden">
              <div className="bg-brand text-white px-4 py-3 flex items-center gap-3">
                <div className="size-10 rounded-full bg-white/20 grid place-items-center text-lg font-semibold">N</div>
                <div className="flex-1">
                  <div className="font-semibold text-sm">Natasha · Andrade & Lemos</div>
                  <div className="text-[11px] opacity-80 flex items-center gap-1">
                    <span className="size-1.5 rounded-full bg-emerald-300 animate-pulse" /> online · responde agora
                  </div>
                </div>
              </div>
              <div className="whatsapp-bg-light dark:whatsapp-bg p-4 space-y-2 min-h-[400px]">
                <ChatBubble side="left" delay={0.4}>Olá! Aqui é do escritório Andrade & Lemos. Vi que você quer entender se o reajuste do seu plano pode ser abusivo.</ChatBubble>
                <ChatBubble side="left" delay={0.9}>Vou te fazer 5 perguntas rápidas para entender seu caso 🙂</ChatBubble>
                <ChatBubble side="right" delay={1.4}>Pode mandar!</ChatBubble>
                <ChatBubble side="left" delay={1.9}>Valor atual? Operadora? Modalidade (individual, empresarial, adesão)? Beneficiários da mesma família? Ano de contratação?</ChatBubble>
                <ChatBubble side="right" delay={2.4}>R$ 2.099 / Porto / empresarial / sim, eu, esposa e filho / 2018</ChatBubble>
                <ChatBubble side="left" delay={2.9}>✅ <strong>Falso coletivo confirmado.</strong> Possível reduzir mensalidade em até 50% e recuperar até 3 anos pagos a mais.</ChatBubble>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="container max-w-6xl mx-auto px-6 py-10 grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat number="até 50%" label="Redução de mensalidade" />
        <Stat number="3 anos" label="Restituição retroativa" />
        <Stat number="30 min" label="Consulta com Dr. Filipe" />
        <Stat number="24/7" label="Atendimento via IA" />
      </section>

      <section id="como-funciona" className="bg-muted/30 border-y py-20">
        <div className="container max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">Em 3 passos simples</h2>
            <p className="text-muted-foreground mt-2">Da primeira mensagem à consulta marcada — tudo pelo WhatsApp</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            <Step n="1" icon={MessageCircle} title="Conversa pelo WhatsApp" desc="Natasha (nossa IA jurídica) faz 5 perguntas rápidas: valor atual, operadora, modalidade, beneficiários e ano de contratação. Aceita texto, áudio ou foto do boleto." />
            <Step n="2" icon={FileSearch} title="Diagnóstico automático" desc="Em segundos a Natasha classifica seu caso em 1 de 5 cenários jurídicos e te explica se o reajuste é abusivo, com base na ANS e jurisprudência atual." />
            <Step n="3" icon={Calendar} title="Consulta com o Dr. Filipe" desc="Se o caso for viável, ela consulta a agenda real do Dr. Filipe Lima e te propõe 2 horários disponíveis. Consulta de 30 min por WhatsApp ou vídeo." />
          </div>
        </div>
      </section>

      <section id="cenarios" className="py-20">
        <div className="container max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">Os 5 cenários que analisamos</h2>
            <p className="text-muted-foreground mt-2">Análise técnica criteriosa antes de qualquer compromisso</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Scenario tone="success" title="Falso Coletivo" tag="Viável" desc="Plano vendido como empresarial mas com beneficiários da mesma família. Caso de maior taxa de êxito — redução até 50% + restituição." />
            <Scenario tone="info" title="Multifamiliar" tag="Viável" desc="Empresarial com beneficiários de famílias diferentes. Tese menos óbvia mas ainda viável, especialmente em planos acima de R$ 10 mil." />
            <Scenario tone="warning" title="Coletivo por Adesão" tag="Avaliar vínculo" desc="Sindicato/associação. Avaliamos vínculo com a entidade. Sem vínculo efetivo = falso coletivo por adesão, também passível de revisão." />
            <Scenario tone="secondary" title="Individual/Familiar" tag="Parcialmente viável" desc="Reajuste regulado pela ANS. Verificamos se houve cobrança indevida e se o índice aplicado foi correto." />
            <Scenario tone="danger" title="Inviável" tag="Sem fundamento" desc="Autogestão (GEAP, Cassi), planos cancelados ou servidores com plano estatal. Te explicamos honestamente quando o caso não tem fundamento jurídico." />
            <Scenario tone="brand" title="Análise honesta" tag="Transparência" desc="Não vendemos esperança. Se seu caso não tem fundamento, a Natasha te avisa logo na conversa — sem cobrar consulta e sem te fazer perder tempo." />
          </div>
        </div>
      </section>

      <section id="beneficios" className="bg-muted/30 border-y py-20">
        <div className="container max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">Tecnologia + advocacia especializada</h2>
            <p className="text-muted-foreground mt-2">Atendimento jurídico com a velocidade da IA e a profundidade humana</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Feature icon={Bot} title="Atendimento por IA 24/7" desc="Natasha responde a qualquer hora, agenda na hora e nunca te deixa esperando. Nem fim de semana, nem feriado." />
            <Feature icon={Mic} title="Aceita áudio" desc="Sem tempo de digitar? Manda áudio que a Natasha transcreve e entende. Inclusive áudios longos." />
            <Feature icon={Camera} title="Aceita foto do boleto" desc="Tira foto do boleto ou contrato e envia. A IA lê e extrai os dados automaticamente." />
            <Feature icon={ShieldCheck} title="Especialistas no tema" desc="Foco exclusivo em planos de saúde e reajustes abusivos. ANS, jurisprudência e operadoras — conhecemos a fundo." />
            <Feature icon={TrendingDown} title="Análise técnica antes" desc="Antes de qualquer compromisso, classificamos seu caso em 5 cenários jurídicos. Você só avança se for viável." />
            <Feature icon={Banknote} title="Honorários conversados" desc="O Dr. Filipe explica valores e funcionamento direto com você na consulta — adaptado ao seu caso. Sem letras miúdas." />
            <Feature icon={Clock} title="100% online" desc="Consulta por WhatsApp ou videoconferência, no horário que for melhor pra você. Sem deslocamento." />
            <Feature icon={Heart} title="Linguagem clara" desc="Nada de juridiquês. Explicamos cada etapa de um jeito que você entende e decide com clareza." />
            <Feature icon={Users} title="Atendimento nacional" desc="Sede em Maceió/AL, mas atendemos clientes de todos os estados — todo o procedimento é digital." />
          </div>
        </div>
      </section>

      <section className="container max-w-5xl mx-auto px-6 py-20">
        <div className="grid md:grid-cols-2 gap-6">
          <Testimonial quote="Eu pagava R$ 2.099 num plano empresarial que era basicamente família. Em poucos meses caiu pra menos da metade e ainda recebi de volta. Atendimento muito direto." author="Cliente — Porto Saúde" stars={5} />
          <Testimonial quote="Achei que ia ser burocrático. A Natasha me explicou tudo no WhatsApp, marquei com o Dr. Filipe pra mesma semana. Em 30 min entendi meu caso melhor do que em anos pagando." author="Cliente — Bradesco Saúde" stars={5} />
        </div>
      </section>

      <section className="container max-w-6xl mx-auto px-6 pb-16">
        <div className="rounded-3xl bg-gradient-to-br from-brand to-brand-dark text-white p-10 md:p-14 text-center shadow-2xl">
          <h2 className="text-3xl md:text-4xl font-bold mb-3">Seu plano subiu de novo este ano?</h2>
          <p className="text-white/90 text-lg mb-6 max-w-2xl mx-auto">
            Em 5 perguntas a Natasha te diz se seu caso é abusivo. Sem cobrar nada para essa primeira análise.
          </p>
          <Button asChild size="lg" variant="secondary" className="h-12 px-6 bg-white text-brand-dark hover:bg-white/90">
            <a href={WHATSAPP_URL} target="_blank" rel="noreferrer">
              <MessageCircle className="size-5 mr-2" /> Falar com Natasha agora
            </a>
          </Button>
          <div className="text-xs text-white/70 mt-4">Resposta em segundos · sem espera · 24h por dia</div>
        </div>
      </section>

      <section id="faq" className="bg-muted/30 border-y py-20">
        <div className="container max-w-3xl mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-10">Perguntas frequentes</h2>
          <div className="space-y-3">
            <FAQ q="O que é &quot;falso coletivo&quot;?" a="É quando uma operadora vende um plano coletivo empresarial para uma família, contornando as regras de reajuste anual dos planos individuais (regulado pela ANS). Como não há vínculo empresarial real, a Justiça vem reconhecendo o direito de reduzir mensalidade e restituir o que foi pago a mais." />
            <FAQ q="Quanto custa a análise inicial?" a="A análise feita pela Natasha no WhatsApp não tem custo. Os honorários do escritório o Dr. Filipe te explica pessoalmente na consulta, conforme o seu caso." />
            <FAQ q="Vocês atendem em qual estado?" a="Sede em Maceió, Alagoas — mas atendemos clientes de todos os estados do Brasil. Todo o procedimento é 100% online (WhatsApp + videoconferência)." />
            <FAQ q="Quanto tempo dura a consulta?" a="A consulta com o Dr. Filipe dura cerca de 30 minutos. Marcada via WhatsApp em horário comercial, dias úteis." />
            <FAQ q="Quais documentos preciso?" a="Para a consulta inicial, basta ter em mãos o último boleto ou o comunicado de reajuste. A Natasha aceita foto ou PDF. Demais documentos só serão pedidos se o caso avançar." />
            <FAQ q="Posso enviar áudio em vez de digitar?" a="Sim! A Natasha entende áudios e fotos. Você pode mandar pelo WhatsApp do jeito que for mais confortável." />
            <FAQ q="Em quanto tempo recebo resposta?" a="A Natasha responde em segundos no WhatsApp, 24h por dia. A consulta com o Dr. Filipe normalmente é marcada para o mesmo dia ou nos próximos dias úteis." />
            <FAQ q="Meu plano é Cassi/GEAP — vocês ajudam?" a="Esses casos (autogestão) têm regras próprias e geralmente não se enquadram na tese do falso coletivo. A Natasha te avisa logo na conversa para você não perder tempo." />
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
              Especializados em direito do consumidor e planos de saúde. Atendimento 100% online em todo o Brasil.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-3">Contato</h3>
            <ul className="space-y-1 text-muted-foreground text-xs">
              <li className="flex items-center gap-2"><MessageCircle className="size-3.5" /> WhatsApp via Natasha (IA jurídica)</li>
              <li className="flex items-center gap-2"><Phone className="size-3.5" /> Maceió, Alagoas · atendimento nacional</li>
              <li className="flex items-center gap-2"><Calendar className="size-3.5" /> Dias úteis 9h–18h (BRT)</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-3">Aviso importante</h3>
            <p className="text-muted-foreground text-[11px] leading-relaxed">
              As informações fornecidas pela Natasha são orientações iniciais e não substituem uma análise jurídica formal pelo advogado responsável. Resultados anteriores não garantem resultados futuros.
            </p>
          </div>
        </div>
        <div className="container max-w-6xl mx-auto px-6 mt-8 text-center text-xs text-muted-foreground border-t pt-6">
          © {new Date().getFullYear()} Andrade & Lemos Advogados · OAB/AL · Maceió, Alagoas
        </div>
      </footer>
    </div>
  );
}

function Stat({ number, label }: { number: string; label: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center">
      <div className="text-3xl md:text-4xl font-bold bg-gradient-to-br from-brand to-brand-dark bg-clip-text text-transparent">{number}</div>
      <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">{label}</div>
    </motion.div>
  );
}

function Step({ n, icon: Icon, title, desc }: any) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="rounded-2xl border bg-card p-6 hover:shadow-lg hover:-translate-y-0.5 transition">
      <div className="size-12 rounded-xl bg-brand/10 text-brand grid place-items-center mb-4"><Icon className="size-6" /></div>
      <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Passo {n}</div>
      <h3 className="font-semibold text-lg mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
    </motion.div>
  );
}

function Feature({ icon: Icon, title, desc }: any) {
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="rounded-xl border bg-card p-5 hover:border-brand/40 transition">
      <div className="size-9 rounded-lg bg-brand/10 text-brand grid place-items-center mb-3"><Icon className="size-5" /></div>
      <h3 className="font-semibold mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
    </motion.div>
  );
}

const TONE_CLASSES: Record<string, string> = {
  success: "border-emerald-500/30 bg-emerald-500/5",
  info: "border-sky-500/30 bg-sky-500/5",
  warning: "border-amber-500/30 bg-amber-500/5",
  secondary: "border-zinc-400/30 bg-zinc-400/5",
  danger: "border-red-500/30 bg-red-500/5",
  brand: "border-brand/30 bg-brand/5",
};
const TONE_TAG: Record<string, string> = {
  success: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  info: "bg-sky-500/15 text-sky-600 dark:text-sky-400",
  warning: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  secondary: "bg-zinc-400/15 text-zinc-600 dark:text-zinc-400",
  danger: "bg-red-500/15 text-red-600 dark:text-red-400",
  brand: "bg-brand/15 text-brand",
};

function Scenario({ tone, title, desc, tag }: { tone: string; title: string; desc: string; tag: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className={`rounded-xl border p-5 ${TONE_CLASSES[tone] || ""}`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3 className="font-semibold">{title}</h3>
        <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full font-medium ${TONE_TAG[tone] || ""}`}>{tag}</span>
      </div>
      <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
    </motion.div>
  );
}

function Testimonial({ quote, author, stars }: { quote: string; author: string; stars: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="rounded-2xl border bg-card p-6">
      <div className="flex gap-0.5 mb-3">
        {[...Array(stars)].map((_, i) => (<Star key={i} className="size-4 fill-amber-400 text-amber-400" />))}
      </div>
      <Quote className="size-5 text-brand/40 mb-2" />
      <p className="text-sm leading-relaxed mb-3 italic">&quot;{quote}&quot;</p>
      <div className="text-xs text-muted-foreground">— {author}</div>
    </motion.div>
  );
}

function FAQ({ q, a }: { q: string; a: string }) {
  return (
    <details className="group rounded-lg border bg-card open:bg-accent/30">
      <summary className="cursor-pointer p-4 font-medium flex items-center justify-between">
        <span dangerouslySetInnerHTML={{ __html: q }} />
        <ArrowRight className="size-4 text-muted-foreground group-open:rotate-90 transition shrink-0" />
      </summary>
      <div className="px-4 pb-4 text-sm text-muted-foreground leading-relaxed">{a}</div>
    </details>
  );
}

function ChatBubble({ side, children, delay }: { side: "left" | "right"; children: React.ReactNode; delay: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.3 }} className={side === "right" ? "flex justify-end" : "flex justify-start"}>
      <div className={side === "right" ? "max-w-[80%] bg-[#d9fdd3] dark:bg-emerald-900/40 text-zinc-900 dark:text-zinc-100 rounded-lg rounded-tr-none px-3 py-2 text-sm shadow-sm" : "max-w-[80%] bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-lg rounded-tl-none px-3 py-2 text-sm shadow-sm"}>
        {children}
      </div>
    </motion.div>
  );
}
