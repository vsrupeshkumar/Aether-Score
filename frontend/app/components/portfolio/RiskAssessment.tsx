'use client';

import { usePortfolio } from '@/app/hooks/usePortfolio';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useWallet } from '@/app/contexts/WalletContext';
import { Loader2, AlertTriangle, CheckCircle, Info } from 'lucide-react';

export function RiskAssessment() {
  const { address } = useWallet();
  const { riskAssessment, isLoading, error } = usePortfolio(address);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk Assessment</CardTitle>
          <CardDescription>Analyzing portfolio risk...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk Assessment</CardTitle>
          <CardDescription>Error loading risk assessment</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error.message}</p>
        </CardContent>
      </Card>
    );
  }

  if (!riskAssessment) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Risk Assessment</CardTitle>
          <CardDescription>Unable to assess risk at this time</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Risk assessment requires sufficient portfolio data.
          </p>
        </CardContent>
      </Card>
    );
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'text-success';
      case 'medium':
        return 'text-warning';
      case 'high':
        return 'text-destructive';
      default:
        return 'text-muted-foreground';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'low':
        return <CheckCircle className="h-5 w-5 text-success" />;
      case 'medium':
        return <Info className="h-5 w-5 text-warning" />;
      case 'high':
        return <AlertTriangle className="h-5 w-5 text-destructive" />;
      default:
        return <Info className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'default';
      case 'low':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Portfolio Risk Assessment</CardTitle>
            <CardDescription>
              Last updated: {riskAssessment.assessment_date ? new Date(riskAssessment.assessment_date).toLocaleDateString() : 'N/A'}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {getRiskIcon(riskAssessment.risk_level)}
            <Badge variant={getSeverityColor(riskAssessment.risk_level)}>
              {riskAssessment.risk_level.toUpperCase()}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Risk Score</span>
            <span className={`text-lg font-bold ${getRiskColor(riskAssessment.risk_level)}`}>
              {riskAssessment.risk_score}/100
            </span>
          </div>
          <Progress value={riskAssessment.risk_score} className="h-2" />
        </div>

        {riskAssessment.risk_factors.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3">Risk Factors</h3>
            <div className="space-y-2">
              {riskAssessment.risk_factors.map((factor, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 border rounded-lg"
                >
                  <Badge variant={getSeverityColor(factor.severity)} className="mt-0.5">
                    {factor.severity}
                  </Badge>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{factor.factor}</p>
                    <p className="text-xs text-muted-foreground mt-1">{factor.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {riskAssessment.recommendations.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3">Recommendations</h3>
            <ul className="space-y-2">
              {riskAssessment.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start gap-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
                  <span>{recommendation}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

