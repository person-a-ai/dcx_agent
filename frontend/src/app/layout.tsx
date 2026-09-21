import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Pretendard 자체 호스팅. UI 는 400/500/600/700 을 쓰고,
// 800 은 수정본의 dominant insight(화면당 하나) 전용이다.
const pretendard = localFont({
  src: [
    { path: "../fonts/Pretendard-Regular.woff2", weight: "400", style: "normal" },
    { path: "../fonts/Pretendard-Medium.woff2", weight: "500", style: "normal" },
    { path: "../fonts/Pretendard-SemiBold.woff2", weight: "600", style: "normal" },
    { path: "../fonts/Pretendard-Bold.woff2", weight: "700", style: "normal" },
    { path: "../fonts/Pretendard-ExtraBold.woff2", weight: "800", style: "normal" },
  ],
  variable: "--font-pretendard",
  display: "swap",
});

export const metadata: Metadata = {
  title: "DCX Pipeline",
  description: "Digital Customer Experience Pipeline",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={pretendard.variable}>
      <body className="font-sans h-screen overflow-hidden antialiased">{children}</body>
    </html>
  );
}
