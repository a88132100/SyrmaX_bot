/**
 * 策略組合包詳細資訊抽屜
 * 
 * 顯示策略組合的完整資訊，包含：
 * - 組合名稱、風格、風險標籤
 * - 組合描述
 * - 子策略完整列表（列表格式：code + 粗體名稱 + summary + indicators）
 * - 底部提示文字（引導前往機器人管理頁）
 */

import React from 'react';
import { X } from 'lucide-react';
import { Drawer } from '@/components/ui/drawer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { getNeutralBadgeStyle, getRiskLevelBadgeStyle } from '@/lib/subtleBadgeStyles';
import { getTagStyle } from './StrategyBundleCard';
import type { StrategyBundleTemplate } from './types';

interface StrategyBundleDetailDrawerProps {
  open: boolean;
  bundle: StrategyBundleTemplate | null;
  onClose: () => void;
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

export function StrategyBundleDetailDrawer({
  open,
  bundle,
  onClose,
}: StrategyBundleDetailDrawerProps) {
  // 沒選東西就不要畫
  if (!bundle) return null;

  return (
    <Drawer isOpen={open} onClose={onClose}>
      <div className="h-full flex flex-col">
        {/* 標題欄 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border flex-shrink-0">
          <div className="flex-1 min-w-0">
            <div className="flex items-center mb-1" style={{ gap: '36px' }}>
              <h2 className="text-lg font-semibold text-text-primary">
                {bundle.name}
              </h2>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span style={getNeutralBadgeStyle()}>
                  {bundle.styleLabel}
                </span>
                <span style={getRiskLevelBadgeStyle(bundle.riskLevel)}>
                  {getRiskLabel(bundle.riskLevel)}
                </span>
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8 flex-shrink-0"
            aria-label="關閉"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* 內容區域 */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
          {/* 組合描述 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">組合說明</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-text-secondary leading-relaxed">
                {bundle.description}
              </p>
              
              {/* Tags（使用 Subtle Badge 風格） */}
              {bundle.tags.length > 0 && (
                <div 
                  className="flex flex-wrap mt-4"
                  style={{ gap: '24px' }}
                >
                  {bundle.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      style={getTagStyle(tag)}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* 子策略完整列表（列表格式） */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                包含策略 ({bundle.includedStrategies.length} 個)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                {bundle.includedStrategies.map((strategy) => (
                  <li key={strategy.code} className="text-sm">
                    {/* 策略代碼與名稱（粗體） */}
                    <div className="font-medium text-text-primary">
                      {strategy.code} {strategy.name}
                    </div>
                    
                    {/* Summary（一般字） */}
                    <div className="mt-1 text-text-secondary leading-relaxed">
                      {strategy.summary}
                    </div>
                    
                    {/* 指標 */}
                    {strategy.indicators.length > 0 && (
                      <div className="mt-1 text-xs text-text-tertiary">
                        指標：{strategy.indicators.join('、')}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* 底部提示文字 */}
          <div className="mt-6 border-t border-border/60 pt-4 text-xs text-text-tertiary">
            本頁僅提供策略與風險說明，如需實際建立或啟動交易機器人，請前往「機器人管理」頁面操作。
          </div>
        </div>
      </div>
    </Drawer>
  );
}
