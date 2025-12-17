import React from 'react'
import { Globe, ChevronDown, Package } from 'lucide-react'
import { Dropdown, DropdownItem } from '@/components/ui/Dropdown'
import { cn } from '@/lib/utils'

type StrategyStyleKey = 'all' | 'aggressive' | 'balanced' | 'conservative'

const STRATEGY_STYLE_FILTERS: { key: StrategyStyleKey; label: string }[] = [
  { key: 'all', label: '所有策略風格' },
  { key: 'aggressive', label: '激進型' },
  { key: 'balanced', label: '平衡型' },
  { key: 'conservative', label: '保守型' },
]

interface TrashToolbarProps {
  exchange?: string
  onExchange: (v?: string) => void
  selectedStyle: StrategyStyleKey
  onStyleChange: (style: StrategyStyleKey) => void
}

// 交易所 Icon 組件 - 實心色塊，使用品牌色
function BinanceIcon({ className }: { className?: string }) {
  return (
    <span 
      className={cn("flex h-5 w-5 items-center justify-center rounded-[4px] flex-shrink-0", className)}
      style={{ backgroundColor: '#F0B90B' }}
    >
      <span className="text-[10px] font-bold leading-none text-white">BN</span>
    </span>
  )
}

function OkxIcon({ className }: { className?: string }) {
  return (
    <span 
      className={cn("flex h-5 w-5 items-center justify-center rounded-[4px] flex-shrink-0", className)}
      style={{ backgroundColor: '#1A1A1A' }}
    >
      <span className="text-[10px] font-bold leading-none text-white">OK</span>
    </span>
  )
}

function BybitIcon({ className }: { className?: string }) {
  return (
    <span 
      className={cn("flex h-5 w-5 items-center justify-center rounded-[4px] flex-shrink-0", className)}
      style={{ backgroundColor: '#F7A600' }}
    >
      <span className="text-[10px] font-bold leading-none text-white">BB</span>
    </span>
  )
}

// 交易所選項配置
interface ExchangeOption {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }> | null
}

const EXCHANGE_OPTIONS: ExchangeOption[] = [
  { id: 'all', label: '所有交易所', icon: Globe },
  { id: 'BINANCE', label: 'BINANCE', icon: BinanceIcon },
  { id: 'OKX', label: 'OKX', icon: OkxIcon },
  { id: 'BYBIT', label: 'BYBIT', icon: BybitIcon },
]

/**
 * 回收桶篩選工具列
 * - 交易所篩選 chip（使用 Dropdown）
 * - 策略包篩選 chip（使用 Dropdown）
 * - 兩個 chip 水平排列，樣式為 filter chip（outline variant, small size）
 */
export function TrashToolbar({
  exchange,
  onExchange,
  selectedStyle,
  onStyleChange,
}: TrashToolbarProps) {
  // 取得當前選中的交易所選項
  const selectedExchange = EXCHANGE_OPTIONS.find(x => x.id === (exchange || 'all')) ?? EXCHANGE_OPTIONS[0]
  const SelectedExchangeIcon = selectedExchange.icon

  // 取得當前選中的策略風格選項
  const selectedStyleOption = STRATEGY_STYLE_FILTERS.find(f => f.key === selectedStyle) ?? STRATEGY_STYLE_FILTERS[0]

  return (
    <div className="flex items-center gap-4">
      {/* 交易所篩選 chip */}
      <Dropdown
        trigger={
          <button
            type="button"
            role="button"
            aria-haspopup="listbox"
            className="inline-flex items-center gap-2 rounded-full border border-border bg-transparent px-3 py-1.5 text-sm text-text-primary hover:border-border/80 hover:bg-background-tertiary cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          >
            <span className="w-4 h-4 flex items-center justify-center flex-shrink-0">
              {SelectedExchangeIcon && <SelectedExchangeIcon className="h-4 w-4" />}
            </span>
            <span className="whitespace-nowrap">{selectedExchange.label}</span>
            <ChevronDown className="w-4 h-4 ml-1 flex-shrink-0 opacity-70" />
          </button>
        }
        align="left"
      >
        {EXCHANGE_OPTIONS.map((option) => {
          const OptionIcon = option.icon
          const isSelected = option.id === (exchange || 'all')
          return (
            <DropdownItem 
              key={option.id} 
              onClick={() => onExchange(option.id === 'all' ? undefined : option.id)}
              className={cn(
                "flex items-center gap-2",
                isSelected && "bg-background-tertiary"
              )}
            >
              <span className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                {OptionIcon && <OptionIcon className="h-5 w-5" />}
              </span>
              <span>{option.label}</span>
            </DropdownItem>
          )
        })}
      </Dropdown>

      {/* 策略風格篩選 chip */}
      <Dropdown
        trigger={
          <button
            type="button"
            role="button"
            aria-haspopup="listbox"
            className="inline-flex items-center gap-2 rounded-full border border-border bg-transparent px-3 py-1.5 text-sm text-text-primary hover:border-border/80 hover:bg-background-tertiary cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          >
            <span className="w-4 h-4 flex items-center justify-center flex-shrink-0">
              <Package className="h-4 w-4 text-text-secondary" />
            </span>
            <span className="whitespace-nowrap">{selectedStyleOption.label}</span>
            <ChevronDown className="w-4 h-4 ml-1 flex-shrink-0 opacity-70" />
          </button>
        }
        align="left"
      >
        {STRATEGY_STYLE_FILTERS.map((filter) => {
          const isSelected = filter.key === selectedStyle
          return (
            <DropdownItem 
              key={filter.key} 
              onClick={() => onStyleChange(filter.key)}
              className={cn(
                "flex items-center gap-2",
                isSelected && "bg-background-tertiary"
              )}
            >
              <span className="w-4 h-4 flex items-center justify-center flex-shrink-0">
                <span className={cn(
                  "h-3 w-3 rounded-full border border-border/60 flex items-center justify-center",
                  isSelected && "bg-emerald-400 border-emerald-400"
                )}>
                  {isSelected && (
                    <span className="h-2 w-2 rounded-full bg-white" />
                  )}
                </span>
              </span>
              <span>{filter.label}</span>
            </DropdownItem>
          )
        })}
      </Dropdown>
    </div>
  )
}

