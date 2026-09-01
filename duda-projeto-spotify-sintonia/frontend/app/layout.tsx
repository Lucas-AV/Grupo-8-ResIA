import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Spotify Insights — UnB',
  description: 'Recomendações musicais explicáveis com clustering e revisão humana.',
};

export default function LayoutRaiz({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}

