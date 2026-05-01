"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/app/components/ui/tabs";
import { Code, Webhook, Package, FileText } from "lucide-react";
import Link from "next/link";

export default function DevelopersPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-4">Developer Portal</h1>
        <p className="text-xl text-gray-600">
          Integrate AETHER-SCORE credit scores into your application
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="api">API Reference</TabsTrigger>
          <TabsTrigger value="webhooks">Webhooks</TabsTrigger>
          <TabsTrigger value="sdk">SDKs</TabsTrigger>
          <TabsTrigger value="widget">Widget</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <Code className="h-8 w-8 mb-2" />
                <CardTitle>RESTful API</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  Query credit scores, loan data, and portfolio information via REST API
                </p>
                <Link href="/developers#api">
                  <Button variant="outline">View API Docs</Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Webhook className="h-8 w-8 mb-2" />
                <CardTitle>Webhooks</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  Receive real-time notifications for score updates and loan events
                </p>
                <Link href="/developers#webhooks">
                  <Button variant="outline">Learn More</Button>
                </Link>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Package className="h-8 w-8 mb-2" />
                <CardTitle>SDKs</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">
                  Official SDKs for JavaScript, Python, and more
                </p>
                <Link href="/developers#sdk">
                  <Button variant="outline">Get SDK</Button>
                </Link>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Get Started</CardTitle>
              <CardDescription>Start integrating AETHER-SCORE in minutes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h3 className="font-semibold">1. Get Your API Key</h3>
                <p className="text-sm text-gray-600">
                  Sign up to get your free API key with 100 requests per day
                </p>
                <Button>Sign Up for API Key</Button>
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold">2. Install SDK</h3>
                <div className="bg-gray-100 p-4 rounded font-mono text-sm">
                  npm install @AETHER-SCORE/sdk
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold">3. Make Your First Request</h3>
                <div className="bg-gray-100 p-4 rounded font-mono text-sm">
                  {`const sdk = new AETHER-SCORESDK({ apiKey: 'your-key' });
const score = await sdk.getScore('0x...');`}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Reference</CardTitle>
              <CardDescription>Complete API documentation</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="mb-4">
                View the complete API documentation with examples and code snippets.
              </p>
              <Link href="/docs/API.md" target="_blank">
                <Button>View Full API Docs</Button>
              </Link>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="webhooks" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Webhooks</CardTitle>
              <CardDescription>Real-time event notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Available Events</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li><code>score.updated</code> - Credit score changed</li>
                  <li><code>loan.created</code> - New loan created</li>
                  <li><code>loan.repaid</code> - Loan repaid</li>
                  <li><code>loan.defaulted</code> - Loan defaulted</li>
                  <li><code>achievement.unlocked</code> - Achievement unlocked</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Webhook Payload</h3>
                <div className="bg-gray-100 p-4 rounded font-mono text-sm">
                  {`{
  "event": "score.updated",
  "timestamp": "2025-12-18T12:00:00Z",
  "data": {
    "address": "0x...",
    "old_score": 700,
    "new_score": 750
  }
}`}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sdk" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>JavaScript/TypeScript</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-gray-100 p-4 rounded font-mono text-sm">
                  npm install @AETHER-SCORE/sdk
                </div>
                <div className="bg-gray-100 p-4 rounded font-mono text-sm">
                  {`import AETHER-SCORESDK from '@AETHER-SCORE/sdk';

const sdk = new AETHER-SCORESDK({
  apiKey: 'your-key'
});

const score = await sdk.getScore('0x...');`}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Python</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-gray-100 p-4 rounded font-mono text-sm">
                  pip install AETHER-SCORE-sdk
                </div>
                <div className="bg-gray-100 p-4 rounded font-mono text-sm">
                  {`from AETHER-SCORE import AETHER-SCOREClient

client = AETHER-SCOREClient(api_key='your-key')
score = client.get_score('0x...')`}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="widget" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Embeddable Widget</CardTitle>
              <CardDescription>One-click integration for your dApp</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Quick Integration</h3>
                <div className="bg-gray-100 p-4 rounded font-mono text-sm">
                  {`<script 
  src="https://AETHER-SCORE.io/widget/embed.js"
  data-address="0x..."
  data-container="AETHER-SCORE-widget">
</script>
<div id="AETHER-SCORE-widget"></div>`}
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Manual Integration</h3>
                <div className="bg-gray-100 p-4 rounded font-mono text-sm">
                  {`AETHER-SCORE.createWidget({
  address: '0x...',
  containerId: 'widget-container',
  apiKey: 'your-key'
});`}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}


