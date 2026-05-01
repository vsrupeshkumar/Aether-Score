'use client';

import { useEffect, useState } from 'react';

interface ScoreDisplayProps {
  score: number;
  riskBand: number;
  explanation: string;
  baseScore?: number;
  stakingBoost?: number;
  oraclePenalty?: number;
}

export default function ScoreDisplay({ 
  score, 
  riskBand, 
  explanation,
  baseScore,
  stakingBoost,
  oraclePenalty
}: ScoreDisplayProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [isAnimating, setIsAnimating] = useState(true);

  useEffect(() => {
    setIsAnimating(true);
    const duration = 2000;
    const steps = 60;
    const increment = score / steps;
    let current = 0;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      current = Math.min(increment * step, score);
      setAnimatedScore(Math.floor(current));
      
      if (step >= steps) {
        setAnimatedScore(score);
        setIsAnimating(false);
        clearInterval(timer);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [score]);

  const getRiskColor = (band: number) => {
    switch (band) {
      case 1: return { gradient: 'from-green-400 to-emerald-500', glow: 'rgba(16, 185, 129, 0.5)', label: 'Low Risk', bg: 'bg-green-500/10', border: 'border-green-500/30' };
      case 2: return { gradient: 'from-amber-400 to-yellow-500', glow: 'rgba(245, 158, 11, 0.5)', label: 'Medium Risk', bg: 'bg-amber-500/10', border: 'border-amber-500/30' };
      case 3: return { gradient: 'from-rose-400 to-red-500', glow: 'rgba(244, 63, 94, 0.5)', label: 'High Risk', bg: 'bg-rose-500/10', border: 'border-rose-500/30' };
      default: return { gradient: 'from-gray-400 to-gray-500', glow: 'rgba(148, 163, 184, 0.5)', label: 'Unknown', bg: 'bg-gray-500/10', border: 'border-gray-500/30' };
    }
  };

  const riskInfo = getRiskColor(riskBand);
  
  // Calculate angle for gauge (0-180 degrees for semicircle)
  const percentage = score / 1000;
  const angle = percentage * 180;
  const circumference = Math.PI * 100; // radius = 100
  const strokeDashoffset = circumference - (percentage * circumference);

  // Get gradient colors based on score
  const getScoreGradient = () => {
    if (score >= 750) return 'from-green-400 via-cyan-400 to-green-500';
    if (score >= 500) return 'from-amber-400 via-yellow-400 to-amber-500';
    return 'from-rose-400 via-red-400 to-rose-500';
  };

  return (
    <div className="glass rounded-2xl p-8 animate-fade-in">
      <h2 className="text-2xl font-bold text-center mb-8 gradient-text">
        Your Credit Score
      </h2>
      
      {/* Radial Gauge */}
      <div className="relative w-80 h-40 mx-auto mb-8">
        <svg className="w-full h-full" viewBox="0 0 200 120" style={{ filter: `drop-shadow(0 0 20px ${riskInfo.glow})` }}>
          <defs>
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00d4ff" />
              <stop offset="50%" stopColor="#7c3aed" />
              <stop offset="100%" stopColor="#00d4ff" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          {/* Background arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth="12"
            strokeLinecap="round"
          />
          
          {/* Score arc with animation */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#scoreGradient)"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="animate-draw-arc"
            style={{ 
              filter: `drop-shadow(0 0 10px ${riskInfo.glow})`,
              transform: 'rotate(180deg)',
              transformOrigin: '100px 100px'
            }}
          />
          
          {/* Score text with glow */}
          <text
            x="100"
            y="75"
            textAnchor="middle"
            className="text-5xl font-bold fill-white"
            style={{ filter: 'url(#glow)' }}
          >
            {animatedScore}
          </text>
          <text
            x="100"
            y="95"
            textAnchor="middle"
            className="text-sm fill-text-secondary"
          >
            / 1000
          </text>
        </svg>
        
        {/* Pulsing glow effect when animating */}
        {isAnimating && (
          <div 
            className="absolute inset-0 rounded-full animate-pulse-glow"
            style={{ 
              background: `radial-gradient(circle, ${riskInfo.glow} 0%, transparent 70%)`,
              pointerEvents: 'none'
            }}
          />
        )}
      </div>

      {/* Risk Band Badge */}
      <div className="text-center mb-6">
        <span className={`inline-flex items-center gap-2 px-6 py-2 rounded-full text-sm font-semibold ${riskInfo.bg} ${riskInfo.border} border`}>
          <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${riskInfo.gradient} animate-pulse`}></div>
          {riskInfo.label}
        </span>
      </div>

      {/* Explanation */}
      <div className="glass-hover rounded-lg p-4 mb-6">
        <p className="text-sm text-text-secondary leading-relaxed">{explanation}</p>
      </div>

      {/* Score Breakdown */}
      {(stakingBoost !== undefined && stakingBoost > 0) || (oraclePenalty !== undefined && oraclePenalty > 0) ? (
        <div className="glass-hover rounded-lg p-6 space-y-4">
          <h3 className="font-semibold text-lg mb-4 gradient-text">Score Breakdown</h3>
          
          {/* Base Score */}
          {baseScore !== undefined && (
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">Base Score</span>
                <span className="font-mono font-semibold text-white">{baseScore}</span>
              </div>
              <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full transition-all duration-1000"
                  style={{ width: `${(baseScore / 1000) * 100}%` }}
                />
              </div>
            </div>
          )}
          
          {/* Oracle Penalty */}
          {oraclePenalty !== undefined && oraclePenalty > 0 && (
            <div className="space-y-2 animate-slide-up stagger-1">
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">Oracle Penalty</span>
                <span className="font-mono font-semibold text-red-400">-{oraclePenalty}</span>
              </div>
              <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-red-500 to-rose-500 rounded-full transition-all duration-1000"
                  style={{ width: `${(oraclePenalty / 1000) * 100}%` }}
                />
              </div>
            </div>
          )}
          
          {/* Staking Boost */}
          {stakingBoost !== undefined && stakingBoost > 0 && (
            <div className="space-y-2 animate-slide-up stagger-2">
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">Staking Boost</span>
                <span className="font-mono font-semibold text-green-400">+{stakingBoost}</span>
              </div>
              <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all duration-1000"
                  style={{ width: `${(stakingBoost / 1000) * 100}%` }}
                />
              </div>
            </div>
          )}
          
          {/* Final Score */}
          <div className="pt-4 border-t border-white/10 space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-semibold text-white">Final Score</span>
              <span className="font-mono font-bold text-2xl gradient-text">{score}</span>
            </div>
            <div className="h-3 bg-white/5 rounded-full overflow-hidden">
              <div 
                className={`h-full bg-gradient-to-r ${getScoreGradient()} rounded-full transition-all duration-1000 glow-gradient`}
                style={{ width: `${(score / 1000) * 100}%` }}
              />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
