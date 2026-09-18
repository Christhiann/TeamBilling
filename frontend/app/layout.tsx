import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'TeamBilling',
  description: 'MVP de billing e multi-tenancy',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
