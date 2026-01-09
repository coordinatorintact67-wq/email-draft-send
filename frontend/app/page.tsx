import Link from 'next/link';
import { Mail, FileEdit } from 'lucide-react';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 relative overflow-hidden">
      {/* Background blobs for premium feel */}
      <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-blue-500/20 rounded-full blur-[100px] -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-purple-500/20 rounded-full blur-[100px] translate-x-1/2 translate-y-1/2" />

      <div className="z-10 text-center space-y-8 glass-panel p-12 rounded-2xl w-full max-w-2xl border border-white/10">
        <h1 className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
          Email Automation
        </h1>
        <p className="text-gray-400 text-lg">
          Manage your outreach campaigns efficiently. Select a mode to begin.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
          <Link
            href="/draft"
            className="group relative p-8 rounded-xl bg-white/5 border border-white/10 hover:border-blue-500/50 hover:bg-white/10 transition-all duration-300 flex flex-col items-center gap-4"
          >
            <div className="p-4 rounded-full bg-blue-500/20 text-blue-400 group-hover:scale-110 transition-transform">
              <FileEdit size={32} />
            </div>
            <h2 className="text-xl font-semibold">Email Draft</h2>
            <p className="text-sm text-gray-500">Preview and save drafts to your folder</p>
          </Link>

          <Link
            href="/send"
            className="group relative p-8 rounded-xl bg-white/5 border border-white/10 hover:border-green-500/50 hover:bg-white/10 transition-all duration-300 flex flex-col items-center gap-4"
          >
            <div className="p-4 rounded-full bg-green-500/20 text-green-400 group-hover:scale-110 transition-transform">
              <Mail size={32} />
            </div>
            <h2 className="text-xl font-semibold">Email Send</h2>
            <p className="text-sm text-gray-500">Directly send emails to recipients</p>
          </Link>
        </div>
      </div>
    </main>
  );
}
