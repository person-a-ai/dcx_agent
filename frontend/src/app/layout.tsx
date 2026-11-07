import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  // Pipeline pages set a per-step <title> (app/pipeline/layout.tsx); a static title here would override it.
  description: "Digital Customer Experience Pipeline",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
