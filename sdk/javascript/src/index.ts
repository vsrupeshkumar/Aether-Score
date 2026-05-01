/**
 * AETHER-SCORE JavaScript/TypeScript SDK
 */
import axios, { AxiosInstance } from 'axios';
import crypto from 'crypto';

export interface AETHER-SCOREConfig {
  apiKey: string;
  baseURL?: string;
}

export interface ScoreResponse {
  address: string;
  score: number;
  risk_band: number;
  last_updated: string;
}

export interface ScoreHistoryResponse {
  address: string;
  history: Array<{
    score: number;
    risk_band: number;
    computed_at: string | null;
  }>;
}

export interface LoanResponse {
  address: string;
  loans: any[];
}

export interface PortfolioResponse {
  address: string;
  total_value: number;
  holdings: any[];
}

export interface WebhookConfig {
  url: string;
  events: string[];
}

export interface WebhookResponse {
  id: number;
  url: string;
  events: string[];
  secret: string;
  created_at: string;
}

export class AETHER-SCORESDK {
  private client: AxiosInstance;
  private apiKey: string;

  constructor(config: AETHER-SCOREConfig) {
    this.apiKey = config.apiKey;
    this.client = axios.create({
      baseURL: config.baseURL || 'https://AETHER-SCORE-backend.onrender.com',
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Get credit score for an address
   */
  async getScore(address: string): Promise<ScoreResponse> {
    const response = await this.client.get(`/api/v1/score/${address}`);
    return response.data;
  }

  /**
   * Get score history for an address
   */
  async getScoreHistory(address: string, limit: number = 30): Promise<ScoreHistoryResponse> {
    const response = await this.client.get(`/api/v1/score/${address}/history`, {
      params: { limit },
    });
    return response.data;
  }

  /**
   * Get loans for an address
   */
  async getLoans(address: string): Promise<LoanResponse> {
    const response = await this.client.get(`/api/v1/loans/${address}`);
    return response.data;
  }

  /**
   * Get portfolio data for an address
   */
  async getPortfolio(address: string): Promise<PortfolioResponse> {
    const response = await this.client.get(`/api/v1/portfolio/${address}`);
    return response.data;
  }

  /**
   * Register a webhook
   */
  async registerWebhook(config: WebhookConfig): Promise<WebhookResponse> {
    const response = await this.client.post('/api/v1/webhooks', config);
    return response.data;
  }

  /**
   * Delete a webhook
   */
  async deleteWebhook(webhookId: number): Promise<{ success: boolean }> {
    const response = await this.client.delete(`/api/v1/webhooks/${webhookId}`);
    return response.data;
  }

  /**
   * Verify webhook signature
   */
  verifyWebhookSignature(
    payload: string,
    signature: string,
    secret: string
  ): boolean {
    const hmac = crypto.createHmac('sha256', secret);
    const expectedSignature = `sha256=${hmac.update(payload).digest('hex')}`;
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  }
}

export default AETHER-SCORESDK;


