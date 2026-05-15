"use client";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Sidebar, MobileNav } from "./sidebar";
import { CommandPalette } from "./command-palette";

const PUBLIC_ROUTES = ["/", "/login"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);

  const isPublic = PUBLIC_ROUTES.includes(pathname);

  useEffect(() => {
    if (isPublic) {
      setReady(true);
      return;
    }
    const creds = sessionStorage.getItem("admin_creds");
    if (!creds) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [pathname, isPublic, router]);

  if (!ready) return null;
  if (isPublic) return <>{children}</>;
  return (
    <>
      <div className="flex min-h-screen bg-background">
        <Sidebar />
        <main className="flex-1 pb-20 lg:pb-0">{children}</main>
      </div>
      <MobileNav />
      <CommandPalette />
    </>
  );
}
