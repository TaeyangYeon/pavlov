import React from 'react'
import { ErrorBoundary } from '../common'

interface MainContentProps {
  children: React.ReactNode
  title?: string
}

export function MainContent({ children, title }: MainContentProps) {
  return (
    <main className="main-content">
      {title && (
        <div className="mb-4">
          <h2 style={{ fontSize: '24px', fontWeight: '600', color: 'var(--color-text)', margin: 0 }}>
            {title}
          </h2>
        </div>
      )}
      <ErrorBoundary>
        {children}
      </ErrorBoundary>
    </main>
  )
}