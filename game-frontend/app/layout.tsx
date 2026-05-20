import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Coven Traders — Idle RPG Trading Game",
  description: "Command AI disciple fleets that trade real USDC across the galaxy. Idle RPG meets DeFi.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-black text-white min-h-screen font-mono">
        {children}
      </body>
    </html>
  );
}
