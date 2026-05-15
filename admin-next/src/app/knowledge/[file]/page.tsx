"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft, Save, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea, Skeleton } from "@/components/ui/index";

export default function KnowledgeEditor() {
  const { file } = useParams<{ file: string }>();
  const decoded = decodeURIComponent(file);
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["knowledge", decoded],
    queryFn: () => api.knowledgeGet(decoded),
  });
  const [content, setContent] = useState("");
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (data?.content !== undefined) {
      setContent(data.content);
      setDirty(false);
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: (v: string) => api.knowledgeSave(decoded, v),
    onSuccess: () => {
      toast.success("Arquivo salvo. RAG vai reindexar.", { description: decoded });
      qc.invalidateQueries({ queryKey: ["knowledge"] });
      qc.invalidateQueries({ queryKey: ["knowledge", decoded] });
      setDirty(false);
    },
    onError: (e: any) => toast.error("Erro ao salvar", { description: String(e?.message || e) }),
  });

  return (
    <>
      <PageHeader
        title={decoded}
        description="Editor de knowledge base · backup automático + reindex"
        action={
          <div className="flex items-center gap-2">
            <Link href="/knowledge">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="size-4 mr-1" /> Voltar
              </Button>
            </Link>
            <Button
              size="sm"
              disabled={!dirty || mutation.isPending}
              onClick={() => mutation.mutate(content)}
            >
              {mutation.isPending ? (
                <RefreshCw className="size-4 mr-1 animate-spin" />
              ) : (
                <Save className="size-4 mr-1" />
              )}
              Salvar
            </Button>
          </div>
        }
      />
      <div className="p-6">
        <Card>
          <CardContent className="p-2">
            {isLoading ? (
              <Skeleton className="h-[70vh]" />
            ) : (
              <Textarea
                value={content}
                onChange={(e) => {
                  setContent(e.target.value);
                  setDirty(true);
                }}
                className="font-mono text-sm h-[70vh] resize-none border-0 focus-visible:ring-0"
                spellCheck={false}
              />
            )}
          </CardContent>
        </Card>
        <div className="text-xs text-muted-foreground mt-3">
          {dirty && <span className="text-amber-500">● Alterações não salvas</span>}
          {!dirty && data && <span>{content.length.toLocaleString("pt-BR")} caracteres</span>}
        </div>
      </div>
    </>
  );
}
