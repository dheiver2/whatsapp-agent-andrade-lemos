"use client";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "./ui/button";

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  destructive,
  loading,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  destructive?: boolean;
  loading?: boolean;
}) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            onClick={loading ? undefined : onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[92vw] max-w-md rounded-xl border bg-card shadow-2xl"
          >
            <div className="p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div
                  className={`size-10 rounded-lg grid place-items-center ${
                    destructive ? "bg-rose-500/15 text-rose-500" : "bg-primary/15 text-primary"
                  }`}
                >
                  <AlertTriangle className="size-5" />
                </div>
                <h2 className="text-lg font-semibold">{title}</h2>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={onClose} disabled={loading}>
                  Cancelar
                </Button>
                <Button
                  variant={destructive ? "destructive" : "default"}
                  onClick={onConfirm}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="size-4 mr-1.5 animate-spin" /> Executando…
                    </>
                  ) : (
                    "Confirmar"
                  )}
                </Button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
