import type { ReactNode } from 'react'
import BottomNav from './BottomNav'

interface LayoutProps {
  title: string
  action?: ReactNode
  children: ReactNode
}

export default function Layout({ title, action, children }: LayoutProps) {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1>{title}</h1>
        {action && <div>{action}</div>}
      </header>
      <main className="app-content">
        {children}
      </main>
      <BottomNav />
    </div>
  )
}
