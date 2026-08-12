import "./globals.css";

import type { ReactNode } from "react";
import { AuthenticationProvider } from "../components/auth-provider";

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body><AuthenticationProvider>{children}</AuthenticationProvider></body>
    </html>
  );
}
