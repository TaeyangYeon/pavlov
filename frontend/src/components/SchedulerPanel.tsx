import React, { useState, useEffect } from 'react';

interface SchedulerJob {
  id: string;
  name: string;
  next_run: string | null;
  trigger: string;
}

interface RecoveryResult {
  recovered: boolean;
  date: string | null;
  error: string | null;
}

interface RecoveryResponse {
  kr?: RecoveryResult;
  us?: RecoveryResult;
}

interface SchedulerStatus {
  status: string;
  timezone: string;
  jobs: SchedulerJob[];
  recovery_enabled?: boolean;
  max_recovery_days?: number;
}

export const SchedulerPanel: React.FC = () => {
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recoveryLoading, setRecoveryLoading] = useState(false);
  const [recoveryResult, setRecoveryResult] = useState<RecoveryResponse | null>(null);

  const fetchSchedulerStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/scheduler/status');
      if (!response.ok) {
        throw new Error(`Failed to fetch scheduler status: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSchedulerStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const triggerRecovery = async (market?: string) => {
    try {
      setRecoveryLoading(true);
      setRecoveryResult(null);
      
      const url = market 
        ? `/api/v1/scheduler/recover?market=${market}`
        : '/api/v1/scheduler/recover';
      
      const response = await fetch(url, { method: 'POST' });
      if (!response.ok) {
        throw new Error(`Recovery failed: ${response.statusText}`);
      }
      
      const result = await response.json();
      setRecoveryResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Recovery error');
    } finally {
      setRecoveryLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedulerStatus();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchSchedulerStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatNextRun = (isoString: string | null): string => {
    if (!isoString) return 'Not scheduled';
    
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = date.getTime() - now.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
      
      if (diffMs < 0) return 'Overdue';
      if (diffHours === 0) return `${diffMinutes}m`;
      if (diffHours < 24) return `${diffHours}h ${diffMinutes}m`;
      
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ${diffHours % 24}h`;
    } catch {
      return 'Invalid date';
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'running': return 'text-green-600';
      case 'stopped': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getJobIcon = (jobId: string): string => {
    switch (jobId) {
      case 'kr_analysis': return '🇰🇷';
      case 'us_analysis': return '🇺🇸';
      default: return '⏰';
    }
  };

  const formatRecoveryResult = (result: RecoveryResult, market: string): JSX.Element => {
    if (result.recovered) {
      return (
        <div className="flex items-center space-x-2 text-green-600">
          <span>✅</span>
          <span>Recovered {result.date}</span>
        </div>
      );
    } else if (result.error === 'stale') {
      return (
        <div className="flex items-center space-x-2 text-yellow-600">
          <span>⏭️</span>
          <span>Skipped (too old)</span>
        </div>
      );
    } else if (result.error) {
      return (
        <div className="flex items-center space-x-2 text-red-600">
          <span>❌</span>
          <span>Failed: {result.error}</span>
        </div>
      );
    } else {
      return (
        <div className="flex items-center space-x-2 text-gray-600">
          <span>⏭️</span>
          <span>None found</span>
        </div>
      );
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <h2 className="text-xl font-semibold">Loading Scheduler Status...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">📅 Scheduler Status</h2>
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <p className="text-red-800">❌ Error: {error}</p>
          <button 
            onClick={fetchSchedulerStatus}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!schedulerStatus) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold">📅 Scheduler Status</h2>
        <p className="text-gray-500 mt-2">No scheduler data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">📅 Scheduler Status</h2>
          <button 
            onClick={fetchSchedulerStatus}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
          >
            🔄 Refresh
          </button>
        </div>

        <div className="mb-6">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-sm font-medium text-gray-600">Status:</span>
            <span className={`font-semibold ${getStatusColor(schedulerStatus.status)}`}>
              {schedulerStatus.status === 'running' ? '🟢 Running' : '🔴 Stopped'}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-600">Timezone:</span>
            <span className="text-sm text-gray-800">{schedulerStatus.timezone}</span>
          </div>
        </div>

        {/* Recovery Section */}
        {schedulerStatus.recovery_enabled && (
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-4">🔄 Missed Execution Recovery</h3>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-blue-800">
                  Max Recovery Days: {schedulerStatus.max_recovery_days}
                </span>
                <button
                  onClick={() => triggerRecovery()}
                  disabled={recoveryLoading}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {recoveryLoading ? '⏳ Checking...' : '🔍 Check Both Markets'}
                </button>
              </div>
              
              <div className="flex space-x-4">
                <button
                  onClick={() => triggerRecovery('KR')}
                  disabled={recoveryLoading}
                  className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 rounded disabled:opacity-50 transition-colors"
                >
                  🇰🇷 Check KR Only
                </button>
                <button
                  onClick={() => triggerRecovery('US')}
                  disabled={recoveryLoading}
                  className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-800 rounded disabled:opacity-50 transition-colors"
                >
                  🇺🇸 Check US Only
                </button>
              </div>
            </div>

            {recoveryResult && (
              <div className="bg-gray-50 border rounded-lg p-4">
                <h4 className="font-medium mb-3">Recovery Result:</h4>
                <div className="space-y-2">
                  {recoveryResult.kr && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">🇰🇷 KR Market:</span>
                      {formatRecoveryResult(recoveryResult.kr, 'KR')}
                    </div>
                  )}
                  {recoveryResult.us && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">🇺🇸 US Market:</span>
                      {formatRecoveryResult(recoveryResult.us, 'US')}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div>
          <h3 className="text-lg font-medium mb-4">Scheduled Jobs</h3>
          
          {schedulerStatus.jobs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No jobs scheduled</p>
          ) : (
            <div className="space-y-4">
              {schedulerStatus.jobs.map((job) => (
                <div key={job.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-xl">{getJobIcon(job.id)}</span>
                      <span className="font-medium">{job.name}</span>
                    </div>
                    <span className="text-sm text-gray-500">ID: {job.id}</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Next Run:</span>
                      <div className="font-medium">
                        {job.next_run ? (
                          <>
                            <div>{new Date(job.next_run).toLocaleString('ko-KR', {
                              timeZone: 'Asia/Seoul',
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                              second: '2-digit'
                            })}</div>
                            <div className="text-xs text-blue-600">
                              ({formatNextRun(job.next_run)} from now)
                            </div>
                          </>
                        ) : (
                          <span className="text-gray-500">Not scheduled</span>
                        )}
                      </div>
                    </div>
                    
                    <div>
                      <span className="text-gray-600">Schedule:</span>
                      <div className="font-mono text-xs text-gray-800 break-all">
                        {job.trigger}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      <div className="bg-gray-50 px-6 py-3 text-xs text-gray-600 rounded-b-lg">
        <div className="flex items-center justify-between">
          <span>Auto-refresh: 30s</span>
          <span>Last updated: {new Date().toLocaleTimeString('ko-KR')}</span>
        </div>
      </div>
    </div>
  );
};