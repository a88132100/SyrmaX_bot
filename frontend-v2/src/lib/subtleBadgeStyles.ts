/**
 * Subtle Badge 樣式工具
 * 
 * 統一的 Subtle Badge 風格：低飽和背景、淡邊框、文字帶色
 * 用於全站所有 Badge 顯示，保持視覺一致性
 */

import type { CSSProperties } from 'react'

/**
 * Subtle Badge 基礎樣式
 */
const BASE_BADGE_STYLE: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  height: '24px',
  borderRadius: '9999px',
  borderWidth: '1px',
  paddingLeft: '10px',
  paddingRight: '10px',
  fontSize: '12px',
  fontWeight: 500,
  whiteSpace: 'nowrap',
}

/**
 * 風險等級 Badge 樣式（Subtle Badge：低飽和背景、淡邊框、文字帶色）
 */
export function getSeverityBadgeStyle(severity: 'danger' | 'warning' | 'info'): CSSProperties {
  switch (severity) {
    case 'danger':
      // danger: #F05B61
      return {
        ...BASE_BADGE_STYLE,
        backgroundColor: 'rgba(240, 91, 97, 0.1)', // danger/10
        borderColor: 'rgba(240, 91, 97, 0.25)', // danger/25
        color: 'rgba(240, 91, 97, 0.8)', // danger 文字（稍淡）
      }
    case 'warning':
      // warning: #E9A73A
      return {
        ...BASE_BADGE_STYLE,
        backgroundColor: 'rgba(233, 167, 58, 0.1)', // warning/10
        borderColor: 'rgba(233, 167, 58, 0.25)', // warning/25
        color: 'rgba(233, 167, 58, 0.8)', // warning 文字（稍淡）
      }
    case 'info':
      // info: #6CA6FF
      return {
        ...BASE_BADGE_STYLE,
        backgroundColor: 'rgba(108, 166, 255, 0.1)', // info/10
        borderColor: 'rgba(108, 166, 255, 0.25)', // info/25
        color: 'rgba(108, 166, 255, 0.8)', // info 文字（稍淡）
      }
  }
}

/**
 * 成功狀態 Badge 樣式
 */
export function getSuccessBadgeStyle(): CSSProperties {
  // success: #3FBF7F
  return {
    ...BASE_BADGE_STYLE,
    backgroundColor: 'rgba(63, 191, 127, 0.1)', // success/10
    borderColor: 'rgba(63, 191, 127, 0.25)', // success/25
    color: 'rgba(63, 191, 127, 0.8)', // success 文字（稍淡）
  }
}

/**
 * 中性 Badge 樣式（用於事件類型等不需要強調的內容）
 */
export function getNeutralBadgeStyle(): CSSProperties {
  return {
    ...BASE_BADGE_STYLE,
    backgroundColor: 'rgba(255, 255, 255, 0.05)', // white/5
    borderColor: 'rgba(255, 255, 255, 0.1)', // white/10
    color: '#E7EBF1', // text-primary
  }
}

/**
 * 次要 Badge 樣式（用於交易所等次要資訊）
 */
export function getSecondaryBadgeStyle(): CSSProperties {
  return {
    ...BASE_BADGE_STYLE,
    backgroundColor: 'rgba(22, 26, 34, 0.6)', // background-secondary/60
    borderColor: 'rgba(42, 47, 58, 0.6)', // border/60
    color: '#E7EBF1', // text-primary
  }
}

/**
 * 機器人狀態 Badge 樣式映射
 */
export function getBotStatusBadgeStyle(status: 'running' | 'stopped' | 'paused' | 'error' | 'cooling'): CSSProperties {
  switch (status) {
    case 'running':
      return getSuccessBadgeStyle()
    case 'paused':
      return getSeverityBadgeStyle('warning')
    case 'stopped':
      return getNeutralBadgeStyle()
    case 'error':
      return getSeverityBadgeStyle('danger')
    case 'cooling':
      return getSeverityBadgeStyle('info')
  }
}

/**
 * 節點狀態 Badge 樣式映射（良好/警告/錯誤）
 */
export function getNodeStatusBadgeStyle(status: 'good' | 'warning' | 'error'): CSSProperties {
  switch (status) {
    case 'good':
      return getSuccessBadgeStyle()
    case 'warning':
      return getSeverityBadgeStyle('warning')
    case 'error':
      return getSeverityBadgeStyle('danger')
  }
}

/**
 * 風險等級 Badge 樣式映射（低/中/高）
 */
export function getRiskLevelBadgeStyle(riskLevel: 'low' | 'medium' | 'high'): CSSProperties {
  switch (riskLevel) {
    case 'low':
      return getSuccessBadgeStyle()
    case 'medium':
      return getSeverityBadgeStyle('warning')
    case 'high':
      return getSeverityBadgeStyle('danger')
  }
}

