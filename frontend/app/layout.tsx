import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MeetLens",
  description: "Client meetings ko summary aur follow-up items mein badlein",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="wrap">
          <header className="top">
            <h1>
              <a href="/" style={{ color: "inherit" }}>MeetLens</a>
            </h1>
            <p>Client meeting notes → summary + follow-up items · SPM Group 08</p>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
