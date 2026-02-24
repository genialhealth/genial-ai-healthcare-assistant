import type { Metadata, Viewport } from 'next';
import './globals.css';
import { AuthGuard } from '@/components/auth-guard';

export const metadata: Metadata = {
  title: 'Genial Team',
  description: 'AI-powered health information assistant',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="h-full w-full bg-background-primary">
          <AuthGuard>
            {children}
          </AuthGuard>
        </div>
      </body>
    </html>
  );
}
