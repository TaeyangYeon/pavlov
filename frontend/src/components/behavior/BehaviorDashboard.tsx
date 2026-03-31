/**
 * Behavioral Analytics Dashboard
 * Complete behavioral analysis view with 5 main sections
 */

import React, { useState, useEffect } from 'react';
import { getBehaviorReport } from '../../api/behavior';
import { listDecisions } from '../../api/decisions';
import type { BehaviorReportResponse } from '../../api/behavior';
import type { DecisionResponse } from '../../api/decisions';
import { AIAlignmentScore } from './AIAlignmentScore';

export const BehaviorDashboard: React.FC = () => {
  const [report, setReport] = useState<BehaviorReportResponse | null>(null);
  const [decisions, setDecisions] = useState<DecisionResponse[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<number>(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [selectedPeriod]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [behaviorData, decisionsData] = await Promise.all([
        getBehaviorReport(selectedPeriod),
        listDecisions(undefined, selectedPeriod),
      ]);
      
      setReport(behaviorData);
      setDecisions(decisionsData);
    } catch (err) {
      setError('데이터를 불러오는데 실패했습니다.');
      console.error('Failed to load behavior data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPatternTypeIcon = (type: string) => {
    switch (type) {
      case 'rapid_reversal': return '🔄';
      case 'ai_contradiction': return '❌';
      case 'overtrading': return '🔁';
      default: return '⚠️';
    }
  };

  const getPatternTypeName = (type: string) => {
    switch (type) {
      case 'rapid_reversal': return '급격한 반전';
      case 'ai_contradiction': return 'AI 모순';
      case 'overtrading': return '과잉거래';
      default: return '기타 패턴';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">행동 분석 데이터를 불러오는 중...</div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-red-600">{error || '데이터를 찾을 수 없습니다.'}</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">🧠 행동 분석</h1>
        
        {/* Period selector */}
        <div className="flex space-x-2">
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setSelectedPeriod(days)}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                selectedPeriod === days
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {days}일
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Section 1: AI 정렬 점수 */}
        <div className="lg:col-span-1">
          <AIAlignmentScore
            alignmentRate={report.ai_alignment_rate}
            alignmentPct={report.ai_alignment_pct}
            alignmentLabel={report.alignment_label}
            alignmentColor={report.alignment_color}
          />
        </div>

        {/* Section 2: 거래 통계 */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">거래 통계</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{report.total_trades}</div>
                <div className="text-sm text-gray-600">총 거래 수</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{report.avg_holding_days.toFixed(1)}</div>
                <div className="text-sm text-gray-600">평균 보유 일수</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {report.most_traded_ticker || '-'}
                </div>
                <div className="text-sm text-gray-600">최다 거래 종목</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Section 3: 감지된 패턴 */}
      <div className="mt-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">감지된 패턴</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="text-center p-4 bg-yellow-50 rounded">
              <div className="text-xl font-bold text-yellow-600">{report.impulse_trade_count}</div>
              <div className="text-sm text-yellow-700">충동 거래</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded">
              <div className="text-xl font-bold text-red-600">{report.contradiction_count}</div>
              <div className="text-sm text-red-700">AI 모순 거래</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded">
              <div className="text-xl font-bold text-orange-600">{report.cooling_off_warnings_received}</div>
              <div className="text-sm text-orange-700">냉각 기간 경고</div>
            </div>
          </div>
          
          {report.patterns.length > 0 ? (
            <div className="space-y-2">
              {report.patterns.map((pattern, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                  <span className="text-xl">{getPatternTypeIcon(pattern.type)}</span>
                  <div className="flex-1">
                    <div className="font-medium text-sm">
                      {getPatternTypeName(pattern.type)}
                    </div>
                    <div className="text-xs text-gray-600">{pattern.description}</div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(pattern.detected_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              감지된 패턴이 없습니다. 좋습니다! 🎉
            </div>
          )}
        </div>
      </div>

      {/* Section 4: 주의가 필요한 종목 */}
      {report.overtrading_tickers.length > 0 && (
        <div className="mt-6">
          <div className="bg-white rounded-lg border border-orange-200 p-6">
            <h3 className="text-lg font-semibold text-orange-800 mb-4">
              ⚠️ 과잉거래 종목
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {report.overtrading_tickers.map((ticker) => (
                <div key={ticker} className="p-2 bg-orange-50 rounded text-center">
                  <div className="font-medium text-orange-700">{ticker}</div>
                  <div className="text-xs text-orange-600">7일간 3회 이상</div>
                </div>
              ))}
            </div>
            <p className="text-sm text-orange-700 mt-4">
              이 종목들은 최근 7일간 3회 이상 거래되었습니다. 과잉거래를 주의하세요.
            </p>
          </div>
        </div>
      )}

      {/* Section 5: 최근 거래 내역 */}
      <div className="mt-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">최근 거래 내역</h3>
          {decisions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2">종목</th>
                    <th className="text-left py-2">행동</th>
                    <th className="text-left py-2">가격</th>
                    <th className="text-left py-2">AI추천여부</th>
                    <th className="text-left py-2">시간</th>
                  </tr>
                </thead>
                <tbody>
                  {decisions.slice(0, 10).map((decision) => (
                    <tr key={decision.id} className="border-b border-gray-100">
                      <td className="py-2 font-medium">{decision.ticker}</td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          decision.action === 'buy' ? 'bg-green-100 text-green-700' :
                          decision.action === 'sell' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {decision.action.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-2">${decision.price.toFixed(2)}</td>
                      <td className="py-2">
                        {decision.ai_suggested ? (
                          <span className="text-green-600">✅ 일치</span>
                        ) : (
                          <span className="text-red-600">❌ 불일치</span>
                        )}
                      </td>
                      <td className="py-2 text-gray-500">
                        {new Date(decision.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              거래 내역이 없습니다.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};