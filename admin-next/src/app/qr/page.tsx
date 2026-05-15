"use client";
import { ExternalLink } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";

export default function QrPage() {
  const url = "http://187.127.12.125:3001";
  return (
    <>
      <PageHeader
        title="QR Code"
        description="Página pública para conectar o WhatsApp"
        action={
          <a href={url} target="_blank" rel="noreferrer" className="text-sm text-primary flex items-center gap-1.5 hover:underline">
            Abrir em nova aba <ExternalLink className="size-3" />
          </a>
        }
      />
      <div className="p-6">
        <Card>
          <CardContent className="p-0 overflow-hidden">
            <iframe src={url} className="w-full bg-white" style={{ height: "calc(100vh - 200px)" }} />
          </CardContent>
        </Card>
      </div>
    </>
  );
}
