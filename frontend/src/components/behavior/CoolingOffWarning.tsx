/**
 * Cooling-off warning modal component
 * Shows when user tries to trade within cooling-off period
 */

import React from 'react';
import type { CoolingOffStatus } from '../../api/behavior';

interface CoolingOffWarningProps {
  coolingOffStatus: CoolingOffStatus;
  onCancel: () => void;
  onOverride: () => void;
}

export const CoolingOffWarning: React.FC<CoolingOffWarningProps> = ({
  coolingOffStatus,
  onCancel,
  onOverride,
}) => {
  const { ticker, minutes_elapsed, minutes_remaining, last_ai_recommendation } = coolingOffStatus;

  const getRecommendationIcon = (recommendation: string | null) => {
    switch (recommendation) {
      case 'buy': return '📈';
      case 'sell': return '📉';
      case 'hold': return '⏸️';
      case 'full_exit': return '🚪';
      default: return '❓';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            냉각 기간 경고
          </h2>
          
          <div className="text-left space-y-3 mb-6">
            <p className="text-gray-700">
              <strong>{ticker}</strong>에 대한 AI 전략 알림을 받은 지{' '}
              <strong>{Math.floor(minutes_elapsed)}분</strong>이 지났습니다.
            </p>
            
            <p className="text-gray-700">
              냉각 기간: 30분 ({Math.floor(minutes_remaining)}분 남음)
            </p>
            
            {last_ai_recommendation && (
              <p className="text-gray-700">
                마지막 AI 추천:{' '}
                <strong>
                  {last_ai_recommendation.toUpperCase()}{' '}
                  {getRecommendationIcon(last_ai_recommendation)}
                </strong>
              </p>
            )}
            
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mt-4">
              <p className="text-sm text-yellow-800">
                충동적인 거래일 수 있습니다. 잠시 후 다시 검토해 보시겠습니까?
              </p>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
            >
              취소
            </button>
            <button
              onClick={onOverride}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              그래도 진행하기
            </button>
          </div>
          
          <p className="text-xs text-gray-500 mt-3">
            이 경고는 신중한 투자 결정을 돕기 위한 것입니다.
          </p>
        </div>
      </div>
    </div>
  );
};