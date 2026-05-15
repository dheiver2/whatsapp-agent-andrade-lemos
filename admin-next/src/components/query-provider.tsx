"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as React from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [qc] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchInterval: 30_000,
            refetchOnWindowFocus: true,
            retry: 1,
          },
        },
      })
  );
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}
