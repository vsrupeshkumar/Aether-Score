'use client';

import { Layout } from '@/components/layout/Layout';
import { FAQ } from '@/components/help/FAQ';
import { VideoTutorials } from '@/components/help/VideoTutorials';
import { SupportForm } from '@/components/help/SupportForm';
import { BookOpen, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function HelpPage() {
  return (
    <Layout>
      <div className="min-h-screen px-8 lg:px-16 py-12">
        <div className="max-w-6xl mx-auto">
          <div className="mb-12">
            <h1 className="text-4xl font-bold text-gradient mb-2">Help Center</h1>
            <p className="text-muted-foreground">
              Find answers, tutorials, and get support
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8 mb-8">
            <div className="lg:col-span-2 space-y-8">
              <FAQ />
              <VideoTutorials />
            </div>
            <div className="space-y-8">
              <SupportForm />
              <div className="card p-6">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Documentation
                </h3>
                <div className="space-y-2">
                  <Link href="/docs" className="block text-sm text-primary hover:underline">
                    API Documentation <ExternalLink className="inline h-3 w-3 ml-1" />
                  </Link>
                  <Link href="/docs/integration" className="block text-sm text-primary hover:underline">
                    Integration Guide <ExternalLink className="inline h-3 w-3 ml-1" />
                  </Link>
                  <Link href="/docs/developer" className="block text-sm text-primary hover:underline">
                    Developer Guide <ExternalLink className="inline h-3 w-3 ml-1" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

