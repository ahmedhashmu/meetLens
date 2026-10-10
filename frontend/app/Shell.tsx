"use client";

import { usePathname } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/lib/auth";

export function Brand() {
  return (
    <a href="/" className="brand">
      <span className="brand-mark" aria-hidden />
      MeetLens
    </a>
  );
}

export default function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading } = useAuth();

  // Login page has its own full-screen layout
  if (pathname === "/login") return <>{children}</>;

  return (
    <>
      <nav className="nav">
        <div className="nav-inner">
          <Brand />
          {!loading && user && (
            <div className="account">
              <span>{user.email}</span>
              <button type="button" className="link" onClick={() => supabase.auth.signOut()}>
                Log out
              </button>
            </div>
          )}
        </div>
      </nav>
      <div className="page">{children}</div>
      <footer className="footer">MeetLens · Software Project Management, UBIT</footer>
    </>
  );
}
