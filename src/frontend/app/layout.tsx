import type { Metadata } from "next";
import { headers } from "next/headers";
import type { ReactNode } from "react";

import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host");
  const protocol = requestHeaders.get("x-forwarded-proto") ?? "http";
  const baseUrl = host ? `${protocol}://${host}` : "http://localhost:3000";
  const previewUrl = new URL("/og.png", baseUrl).toString();
  return {
    title: "Machinable — Drawing to raw stock",
    description:
      "Review material, dimensions, and raw-stock recommendations from engineering drawings.",
    openGraph: {
      title: "Machinable",
      description: "Engineering drawing review for raw-material planning.",
      images: [{ url: previewUrl, width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title: "Machinable",
      description: "Engineering drawing review for raw-material planning.",
      images: [previewUrl],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
