import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/utils'

interface DropdownProps {
  trigger: React.ReactNode
  children: React.ReactNode
  align?: 'left' | 'right'
  className?: string
}

/**
 * 簡單的下拉選單組件
 * - 點擊觸發器顯示/隱藏選單
 * - 點擊外部或選單項目時關閉
 * - 支援左/右對齊
 */
export function Dropdown({ trigger, children, align = 'right', className }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const triggerRef = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const itemsRef = useRef<HTMLButtonElement[]>([])

  // 取得所有可用的選單項目
  const getMenuItems = (): HTMLButtonElement[] => {
    if (!menuRef.current) return []
    return Array.from(menuRef.current.querySelectorAll('[data-dropdown-item]')) as HTMLButtonElement[]
  }

  // 點擊外部關閉
  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      if (
        triggerRef.current &&
        menuRef.current &&
        !triggerRef.current.contains(event.target as Node) &&
        !menuRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
        setFocusedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  // 鍵盤操作處理
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      const items = getMenuItems()
      
      if (e.key === 'Escape') {
        e.preventDefault()
        setIsOpen(false)
        setFocusedIndex(-1)
        // 將焦點返回觸發按鈕
        const triggerButton = triggerRef.current?.querySelector('button')
        if (triggerButton) {
          triggerButton.focus()
        }
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        const nextIndex = focusedIndex < items.length - 1 ? focusedIndex + 1 : 0
        setFocusedIndex(nextIndex)
        items[nextIndex]?.focus()
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        const prevIndex = focusedIndex > 0 ? focusedIndex - 1 : items.length - 1
        setFocusedIndex(prevIndex)
        items[prevIndex]?.focus()
      } else if (e.key === 'Enter' || e.key === ' ') {
        // Enter 或 Space：如果焦點在選單項目上，觸發點擊
        if (focusedIndex >= 0 && items[focusedIndex]) {
          e.preventDefault()
          items[focusedIndex].click()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, focusedIndex])

  // 當選單開啟時，重置焦點索引
  useEffect(() => {
    if (isOpen) {
      setFocusedIndex(-1)
    }
  }, [isOpen])

  // 計算菜單位置
  const getMenuStyle = (): React.CSSProperties => {
    if (!triggerRef.current || !isOpen) {
      return {}
    }

    const rect = triggerRef.current.getBoundingClientRect()
    return {
      position: 'fixed',
      top: `${rect.bottom}px`, // 緊貼按鈕底部，無間距
      left: `${rect.left}px`,
      width: `${rect.width}px`,
      minWidth: `${rect.width}px`,
      maxWidth: '220px',
    }
  }

  // 處理觸發按鈕的鍵盤事件
  const handleTriggerKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      setIsOpen(!isOpen)
    } else if (e.key === 'ArrowDown' && !isOpen) {
      e.preventDefault()
      setIsOpen(true)
    }
  }

  return (
    <>
      <div
        ref={triggerRef}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleTriggerKeyDown}
        className="inline-block"
      >
        {trigger}
      </div>

      {isOpen &&
        typeof document !== 'undefined' &&
        createPortal(
          <div
            ref={menuRef}
            className={cn(
              'w-full max-w-[220px] rounded-xl border border-border/60 shadow-lg shadow-black/40',
              'animate-in fade-in-0 zoom-in-95 duration-150',
              'overflow-hidden', // 確保圓角正確顯示
              className
            )}
            style={{
              ...getMenuStyle(),
              zIndex: 50,
              backgroundColor: '#0E1116', // 直接使用主背景色
            }}
            onClick={(e) => {
              // 點擊選單項目時關閉
              if ((e.target as HTMLElement).closest('[data-dropdown-item]')) {
                setIsOpen(false)
                setFocusedIndex(-1)
              }
            }}
            role="listbox"
            aria-label="下拉選單"
          >
            {children}
          </div>,
          document.body
        )}
    </>
  )
}

interface DropdownItemProps {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  className?: string
  variant?: 'default' | 'danger'
}

export function DropdownItem({
  children,
  onClick,
  disabled = false,
  className,
  variant = 'default',
}: DropdownItemProps) {
  return (
    <button
      type="button"
      data-dropdown-item
      onClick={onClick}
      disabled={disabled}
      role="option"
      className={cn(
        'w-full px-3 py-2 text-sm text-left transition-colors',
        'first:rounded-t-lg last:rounded-b-lg',
        'border-none shadow-none',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
        variant === 'danger'
          ? 'text-danger hover:bg-danger/10'
          : 'text-text-primary hover:bg-background-tertiary/70',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      style={{
        boxShadow: 'none',
        WebkitAppearance: 'none',
        appearance: 'none',
        backgroundColor: '#0E1116', // 直接使用主背景色
      }}
    >
      {children}
    </button>
  )
}

