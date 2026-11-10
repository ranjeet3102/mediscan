import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Navbar } from '@/components/layout/Navbar';

export const metadata: Metadata = {
  title: 'Medical Report Simplifier 2.0 | AI-Powered Health Literacy',
  description:
    'AI-powered, confidence-aware medical report understanding, comparison, and conversational health-literacy platform.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080c14] text-slate-100 min-h-screen antialiased selection:bg-cyan-500 selection:text-slate-950">
        <AuthProvider>
          <AuthGuard>
            <div className="flex min-h-screen flex-col">
              <Navbar />
              <main className="flex-1 flex flex-col">{children}</main>
            </div>
          </AuthGuard>
        </AuthProvider>
      </body>
    </html>
  );
}
