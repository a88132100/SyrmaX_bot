import { LucideIcon, RefreshCw } from 'lucide-react'
import { SxButton } from './sx-button'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action,
  className 
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 text-center ${className}`}>
      <div className="p-4 rounded-full bg-gold-500/10 mb-4">
        <Icon className="h-12 w-12 text-gold-400" />
      </div>
      <h3 className="text-lg font-semibold text-sx-text mb-2">{title}</h3>
      <p className="text-sx-subtext mb-6 max-w-md">{description}</p>
      {action && (
        <SxButton variant="gold" onClick={action.onClick}>
          {action.label}
        </SxButton>
      )}
    </div>
  )
}

interface ErrorStateProps {
  title?: string
  description?: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({ 
  title = "載入失敗", 
  description = "發生錯誤，請稍後再試", 
  onRetry,
  className 
}: ErrorStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 text-center ${className}`}>
      <div className="p-4 rounded-full bg-danger/10 mb-4">
        <RefreshCw className="h-12 w-12 text-danger" />
      </div>
      <h3 className="text-lg font-semibold text-sx-text mb-2">{title}</h3>
      <p className="text-sx-subtext mb-6 max-w-md">{description}</p>
      {onRetry && (
        <SxButton variant="outline" onClick={onRetry} leftIcon={<RefreshCw className="h-4 w-4" />}>
          重試
        </SxButton>
      )}
    </div>
  )
}