import React, { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="error-state">
          <h3>문제가 발생했습니다</h3>
          <p>페이지에서 오류가 발생했습니다. 페이지를 새로고침해 보세요.</p>
          <button 
            onClick={() => window.location.reload()}
            className="btn btn-primary"
            style={{ marginTop: '16px' }}
          >
            페이지 새로고침
          </button>
          
          {import.meta.env.DEV && this.state.error && (
            <details style={{ marginTop: '16px' }}>
              <summary style={{ cursor: 'pointer', color: 'var(--color-text-secondary)' }}>
                개발자 정보
              </summary>
              <pre style={{ 
                marginTop: '8px', 
                padding: '8px', 
                background: 'var(--color-bg)',
                borderRadius: '4px',
                fontSize: '12px',
                overflow: 'auto'
              }}>
                {this.state.error.stack}
              </pre>
            </details>
          )}
        </div>
      )
    }

    return this.props.children
  }
}