"use client";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (pathname === "/login") {
      setChecked(true);
      return;
    }
    const creds = typeof window !== "undefined" ? sessionStorage.getItem("admin_creds") : null;
    if (!creds) {
      router.replace("/login");
      return;
    }
    setChecked(true);
  }, [pathname, router]);

  if (!checked) return null;
  return <>{children}</>;
}
