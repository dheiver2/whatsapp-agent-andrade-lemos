"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { motion } from "framer-motion";
import { FileText, Edit3 } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/index";

export default function KnowledgePage() {
  const { data, isLoading } = useQuery({ queryKey: ["knowledge"], queryFn: api.knowledgeList });
  return (
    <>
      <PageHeader
        title="Knowledge Base"
        description="Arquivos consultados pela IA via RAG. Editar dispara reindex automático."
      />
      <div className="p-6">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
          {isLoading
            ? [...Array(6)].map((_, i) => <Skeleton key={i} className="h-24" />)
            : (data || []).map((f, i) => (
                <motion.div
                  key={f.name}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                >
                  <Link href={`/knowledge/${encodeURIComponent(f.name)}`}>
                    <Card className="hover:bg-accent/30 hover:border-primary/40 transition cursor-pointer h-full">
                      <CardContent className="p-4 flex items-start gap-3">
                        <div className="size-10 rounded-lg bg-primary/10 text-primary grid place-items-center">
                          <FileText className="size-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{f.name}</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {f.size.toLocaleString("pt-BR")} bytes · modificado {f.modified}
                          </div>
                        </div>
                        <Edit3 className="size-4 text-muted-foreground" />
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
        </div>
      </div>
    </>
  );
}
