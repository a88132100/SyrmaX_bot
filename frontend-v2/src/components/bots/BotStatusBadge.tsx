import { BOT_STATUS_STYLES, type BotStatus } from '@/lib/botStatusStyles'
import { getBotStatusBadgeStyle } from '@/lib/subtleBadgeStyles'

interface BotStatusBadgeProps {
  status: BotStatus
}

/**
 * 機器人狀態徽章元件
 * - 使用 Subtle Badge 風格：低飽和背景、淡邊框、文字帶色
 * - 外部小圓點 + 內部文字膠囊
 */
export function BotStatusBadge({ status }: BotStatusBadgeProps) {
  const style = BOT_STATUS_STYLES[status]
  const badgeStyle = getBotStatusBadgeStyle(status)

  return (
    <div className="flex items-center">
      {/* 外部小圓點 (6px) */}
      <span
        className="h-1.5 w-1.5 rounded-full flex-shrink-0"
        style={{
          backgroundColor: style.dotColor,
          minWidth: '6px',
          minHeight: '6px',
          marginRight: '10px',
        }}
        aria-hidden="true"
      />
      {/* 文字膠囊 - 使用 Subtle Badge 風格 */}
      <span
        style={badgeStyle}
        aria-label={`機器人狀態：${style.label}`}
      >
        {style.label}
      </span>
    </div>
  )
}

