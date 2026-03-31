/**
 * AI Alignment Score visualization component
 * Shows circular progress gauge with color coding
 */

import React from 'react';

interface AIAlignmentScoreProps {
  alignmentRate: number; // 0.0 to 1.0
  alignmentPct: string; // "75.0%"
  alignmentLabel: string;
  alignmentColor: string; // "green" | "yellow" | "orange" | "red"
}

export const AIAlignmentScore: React.FC<AIAlignmentScoreProps> = ({
  alignmentRate,
  alignmentPct,
  alignmentLabel,
  alignmentColor,
}) => {
  const percentage = Math.round(alignmentRate * 100);
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'green':
        return {
          text: 'text-green-600',
          stroke: 'stroke-green-600',
          bg: 'bg-green-50',
          border: 'border-green-200'
        };
      case 'yellow':
        return {
          text: 'text-yellow-600',
          stroke: 'stroke-yellow-600',
          bg: 'bg-yellow-50',
          border: 'border-yellow-200'
        };
      case 'orange':
        return {
          text: 'text-orange-600',
          stroke: 'stroke-orange-600',
          bg: 'bg-orange-50',
          border: 'border-orange-200'
        };
      case 'red':
        return {
          text: 'text-red-600',
          stroke: 'stroke-red-600',
          bg: 'bg-red-50',
          border: 'border-red-200'
        };
      default:
        return {
          text: 'text-gray-600',
          stroke: 'stroke-gray-600',
          bg: 'bg-gray-50',
          border: 'border-gray-200'
        };
    }
  };

  const colors = getColorClasses(alignmentColor);

  return (
    <div className={`p-6 rounded-lg border-2 ${colors.bg} ${colors.border}`}>
      <div className="flex flex-col items-center">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          AI 정렬 점수
        </h3>
        
        {/* Circular Progress */}
        <div className="relative w-32 h-32 mb-4">
          <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
            {/* Background Circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="6"
              className="text-gray-200"
            />
            
            {/* Progress Circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              strokeWidth="6"
              className={colors.stroke}
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              style={{ 
                transition: 'stroke-dashoffset 0.5s ease-in-out' 
              }}
            />
          </svg>
          
          {/* Score Text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className={`text-2xl font-bold ${colors.text}`}>
                {alignmentPct}
              </div>
            </div>
          </div>
        </div>
        
        {/* Label */}
        <p className={`text-sm text-center ${colors.text} font-medium`}>
          {alignmentLabel}
        </p>
        
        {/* Trend indicator placeholder */}
        <div className="mt-2 flex items-center space-x-1">
          <span className="text-xs text-gray-500">
            추세: 
          </span>
          <span className="text-xs text-gray-400">
            → 안정
          </span>
        </div>
      </div>
    </div>
  );
};