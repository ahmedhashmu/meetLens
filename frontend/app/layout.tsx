import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import AccountBadge from "./AccountBadge";

export const metadata: Metadata = {
  title: "MeetLens",
  description: "Turn client meetings into summaries and follow-up items",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <div className="wrap">
            <header className="top">
              <div className="row" style={{ alignItems: "flex-start" }}>
                <div>
                  <h1>
                    <a href="/" style={{ color: "inherit" }}>MeetLens</a>
                  </h1>
                  <p>Client meeting notes → summary + follow-up items · SPM Group 08</p>
                </div>
                <AccountBadge />
              </div>
            </header>
            {children}
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
