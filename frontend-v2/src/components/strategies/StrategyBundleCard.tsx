/**
 * 策略組合包卡片元件（Sales 卡片風格）
 * 
 * 卡片定位：快速掃描與比較的策略選單
 * - 採用類似 Sales 卡片的簡潔風格
 * - 只顯示關鍵摘要資訊
 * - 詳細內容移至 Drawer
 * 
 * 更新時間：2024-12-19 - 改為 Sales 卡片風格
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { getNeutralBadgeStyle, getRiskLevelBadgeStyle } from '@/lib/subtleBadgeStyles';
import type { StrategyBundleTemplate } from './types';

interface StrategyBundleCardProps {
  bundle: StrategyBundleTemplate;
  onViewDetail: () => void;
  highlightBundleId?: string | null;
}

/**
 * 取得風險等級顯示文字
 */
function getRiskLabel(riskLevel: 'low' | 'medium' | 'high'): string {
  switch (riskLevel) {
    case 'low':
      return '低風險';
    case 'medium':
      return '中風險';
    case 'high':
      return '高風險';
  }
}

/**
 * Tag 顏色映射表
 * 使用專案現有的顏色系統（danger, warning, success, info, primary）
 */
const tagColorMap: Record<string, { bg: string; text: string; border: string }> = {
  // 進攻/突破類 - 紅橙色系（danger/warning）
  "突破": { bg: "rgba(240, 91, 97, 0.1)", text: "rgba(240, 91, 97, 0.8)", border: "rgba(240, 91, 97, 0.25)" },
  "短週期": { bg: "rgba(233, 167, 58, 0.1)", text: "rgba(233, 167, 58, 0.8)", border: "rgba(233, 167, 58, 0.25)" },
  "順勢": { bg: "rgba(63, 191, 127, 0.1)", text: "rgba(63, 191, 127, 0.8)", border: "rgba(63, 191, 127, 0.25)" },
  "動量": { bg: "rgba(233, 167, 58, 0.1)", text: "rgba(233, 167, 58, 0.8)", border: "rgba(233, 167, 58, 0.25)" },
  "追價": { bg: "rgba(240, 91, 97, 0.1)", text: "rgba(240, 91, 97, 0.8)", border: "rgba(240, 91, 97, 0.25)" },
  "高波動": { bg: "rgba(240, 91, 97, 0.1)", text: "rgba(240, 91, 97, 0.8)", border: "rgba(240, 91, 97, 0.25)" },
  
  // 均值回歸類 - 藍色系（info/primary）
  "均值回歸": { bg: "rgba(108, 166, 255, 0.1)", text: "rgba(108, 166, 255, 0.8)", border: "rgba(108, 166, 255, 0.25)" },
  "平衡": { bg: "rgba(33, 193, 214, 0.1)", text: "rgba(33, 193, 214, 0.8)", border: "rgba(33, 193, 214, 0.25)" },
  "適應性": { bg: "rgba(108, 166, 255, 0.1)", text: "rgba(108, 166, 255, 0.8)", border: "rgba(108, 166, 255, 0.25)" },
  "靈活": { bg: "rgba(33, 193, 214, 0.1)", text: "rgba(33, 193, 214, 0.8)", border: "rgba(33, 193, 214, 0.25)" },
  
  // 防守/穩健類 - 灰綠色系（success）
  "防守": { bg: "rgba(42, 47, 58, 0.1)", text: "#A6AEC3", border: "rgba(42, 47, 58, 0.25)" },
  "穩健": { bg: "rgba(63, 191, 127, 0.1)", text: "rgba(63, 191, 127, 0.8)", border: "rgba(63, 191, 127, 0.25)" },
  "長期": { bg: "rgba(63, 191, 127, 0.1)", text: "rgba(63, 191, 127, 0.8)", border: "rgba(63, 191, 127, 0.25)" },
  "長期趨勢": { bg: "rgba(63, 191, 127, 0.1)", text: "rgba(63, 191, 127, 0.8)", border: "rgba(63, 191, 127, 0.25)" },
  "多重確認": { bg: "rgba(42, 47, 58, 0.1)", text: "#A6AEC3", border: "rgba(42, 47, 58, 0.25)" },
  "最低風險": { bg: "rgba(42, 47, 58, 0.1)", text: "#A6AEC3", border: "rgba(42, 47, 58, 0.25)" },
  
  // 其他
  "趨勢": { bg: "rgba(33, 193, 214, 0.1)", text: "rgba(33, 193, 214, 0.8)", border: "rgba(33, 193, 214, 0.25)" },
  "濾網": { bg: "rgba(108, 166, 255, 0.1)", text: "rgba(108, 166, 255, 0.8)", border: "rgba(108, 166, 255, 0.25)" },
  "反轉": { bg: "rgba(233, 167, 58, 0.1)", text: "rgba(233, 167, 58, 0.8)", border: "rgba(233, 167, 58, 0.25)" },
  "量能": { bg: "rgba(233, 167, 58, 0.1)", text: "rgba(233, 167, 58, 0.8)", border: "rgba(233, 167, 58, 0.25)" },
  "通道": { bg: "rgba(108, 166, 255, 0.1)", text: "rgba(108, 166, 255, 0.8)", border: "rgba(108, 166, 255, 0.25)" },
  "確認": { bg: "rgba(33, 193, 214, 0.1)", text: "rgba(33, 193, 214, 0.8)", border: "rgba(33, 193, 214, 0.25)" },
  "全策略": { bg: "rgba(42, 47, 58, 0.1)", text: "#A6AEC3", border: "rgba(42, 47, 58, 0.25)" },
};

/**
 * 取得 Tag 樣式（使用 Subtle Badge 風格）
 * 導出以供其他組件使用
 */
export function getTagStyle(tag: string): React.CSSProperties {
  const style = tagColorMap[tag] ?? {
    bg: "rgba(42, 47, 58, 0.1)",
    text: "#A6AEC3",
    border: "rgba(42, 47, 58, 0.25)", // 改為 25% 透明度以符合 Subtle Badge 風格
  };
  
  // 使用 Subtle Badge 基礎樣式
  return {
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
    backgroundColor: style.bg,
    color: style.text,
    borderColor: style.border,
  };
}

export function StrategyBundleCard({ bundle, onViewDetail, highlightBundleId }: StrategyBundleCardProps) {
  // 只顯示所有子策略的名稱（不含 summary）
  const strategyNames = bundle.includedStrategies.map((s) => `${s.code} ${s.name}`);
  const isHighlighted = highlightBundleId === bundle.id;

  return (
    <div
      data-bundle-id={bundle.id}
      className={cn(
        "rounded-xl border border-border/60",
        "bg-background-secondary",
        "hover:border-primary/50 hover:bg-background-secondary/90 transition-colors",
        "px-4 py-4 flex flex-col h-full",
        isHighlighted && "ring-2 ring-primary/50 border-primary/50"
      )}
      style={{
        backgroundColor: '#161A22',
        borderColor: isHighlighted ? 'rgba(33, 193, 214, 0.5)' : 'rgba(42, 47, 58, 0.6)',
        minHeight: '280px',
      }}
    >
      {/* 頂部：標題（左上）與 Badge（右上） */}
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-medium text-text-secondary">
          {bundle.name}
        </h3>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span style={getNeutralBadgeStyle()}>
            {bundle.styleLabel}
          </span>
          <span style={getRiskLevelBadgeStyle(bundle.riskLevel)}>
            {getRiskLabel(bundle.riskLevel)}
          </span>
        </div>
      </div>

      {/* 主要內容：描述文字 */}
      <p className="text-sm text-text-secondary mb-3 line-clamp-2 flex-1">
        {bundle.description}
      </p>

      {/* Tags - 膠囊樣式（最多顯示 3 個） */}
      {bundle.tags.length > 0 && (
        <div 
          className="flex flex-wrap mb-3"
          style={{ gap: '24px' }}
        >
          {bundle.tags.slice(0, 3).map((tag, idx) => (
            <span
              key={idx}
              style={getTagStyle(tag)}
            >
              {tag}
            </span>
          ))}
          {bundle.tags.length > 3 && (
            <span style={getNeutralBadgeStyle()}>
              +{bundle.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* 包含策略：顯示為主要數字（類似 Sales 卡片的大數字） */}
      <div className="mt-auto mb-3">
        <div className="text-2xl font-semibold text-text-primary mb-1">
          {bundle.includedStrategies.length} 個策略
        </div>
        <p className="text-xs text-text-tertiary">
          {strategyNames.slice(0, 2).join('、')}
          {bundle.includedStrategies.length > 2 && ' 等'}
        </p>
      </div>

      {/* 底部：查看詳細按鈕 */}
      <div className="pt-3 border-t border-border/40">
        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onViewDetail();
          }}
          className="w-full text-sm cursor-pointer hover:bg-background-secondary"
          type="button"
        >
          查看詳細
        </Button>
      </div>
    </div>
  );
}
