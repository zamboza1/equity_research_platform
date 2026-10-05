import type { Metadata } from 'next';

import './globals.css';
import Sidebar from '@/components/Sidebar';
import DataStatus from '@/components/DataStatus';
import { AssumptionsProvider } from '@/context/AssumptionsContext';



export const metadata: Metadata = {
  title: 'Vertige | Equity Research',
  description: 'Financial models, assumptions and research',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <AssumptionsProvider>
          <div className="flex bg-[#F8FAFC] min-h-screen">
            <Sidebar />
            <main className="flex-1 min-w-0 p-4 md:p-8 transition-all duration-300 ml-16 md:ml-[var(--sidebar-width,240px)]">
              <DataStatus />
              {children}
            </main>
          </div>
        </AssumptionsProvider>
      </body>
    </html>
  );
}
