/**
 * 策略管理頁面
 * 
 * 功能定位：策略組合說明中心 + 查看詳細
 * - 不負責建立/啟動機器人（建立機器人流程在「機器人管理」頁）
 * - 兩階段選擇：先選風格 → 再選具體策略組合 → 查看詳細說明
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { STRATEGY_BUNDLES } from '@/components/strategies/strategyBundles';
import type { StrategyBundleTemplate } from '@/components/strategies/types';
import { StrategyStyleCard, type StrategyStyle } from '@/components/strategies/StrategyStyleCard';
import { StrategyBundleList } from '@/components/strategies/StrategyBundleList';
import { StrategyBundleDetailDrawer } from '@/components/strategies/StrategyBundleDetailDrawer';

export default function Strategies() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const [selectedStyle, setSelectedStyle] = useState<StrategyStyle | null>(null);
  const [selectedBundle, setSelectedBundle] = useState<StrategyBundleTemplate | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [highlightBundleId, setHighlightBundleId] = useState<string | null>(null);

  // 依風格分類策略組合包
  const aggressiveBundles = STRATEGY_BUNDLES.filter((b) => b.style === 'aggressive');
  const balancedBundles = STRATEGY_BUNDLES.filter((b) => b.style === 'balanced');
  const conservativeBundles = STRATEGY_BUNDLES.filter((b) => b.style === 'conservative');

  // 處理查看詳細
  const handleViewDetail = (bundle: StrategyBundleTemplate) => {
    setSelectedBundle(bundle);
    setIsDetailOpen(true);
  };

  // 處理 query 參數：自動選中風格、展開列表、定位到 bundle、打開 Drawer
  useEffect(() => {
    const qsStyle = searchParams.get('style') as StrategyStyle | null;
    const qsBundle = searchParams.get('bundle');

    if (qsStyle && ['aggressive', 'balanced', 'conservative'].includes(qsStyle)) {
      // 1. 選中對應風格
      setSelectedStyle(qsStyle);

      // 2. 等待風格卡片展開後，找到對應的 bundle
      if (qsBundle) {
        const decodedBundleId = decodeURIComponent(qsBundle);
        const targetBundle = STRATEGY_BUNDLES.find(b => b.id === decodedBundleId);

        if (targetBundle) {
          // 使用 setTimeout 確保 DOM 已渲染
          setTimeout(() => {
            // 3. 定位到 bundle（scroll into view）
            const bundleElement = document.querySelector(`[data-bundle-id="${decodedBundleId}"]`);
            if (bundleElement) {
              bundleElement.scrollIntoView({ behavior: 'smooth', block: 'center' });

              // 4. 高亮顯示（1.5 秒後清除）
              setHighlightBundleId(decodedBundleId);
              setTimeout(() => {
                setHighlightBundleId(null);
              }, 1500);

              // 5. 打開 Drawer
              setSelectedBundle(targetBundle);
              setIsDetailOpen(true);
            }
          }, 300); // 等待風格卡片展開動畫完成
        }
      }
    } else if (qsBundle) {
      // 如果只有 bundle 參數，嘗試從 bundle id 推斷 style
      const decodedBundleId = decodeURIComponent(qsBundle);
      const targetBundle = STRATEGY_BUNDLES.find(b => b.id === decodedBundleId);
      if (targetBundle) {
        setSelectedStyle(targetBundle.style);
        setTimeout(() => {
          const bundleElement = document.querySelector(`[data-bundle-id="${decodedBundleId}"]`);
          if (bundleElement) {
            bundleElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setHighlightBundleId(decodedBundleId);
            setTimeout(() => {
              setHighlightBundleId(null);
            }, 1500);
            setSelectedBundle(targetBundle);
            setIsDetailOpen(true);
          }
        }, 300);
      }
    }
  }, [searchParams]);

  return (
    <div className="p-6 space-y-6">
      {/* 頁首標題區 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">
            {t('strategies.title')}
          </h1>
          <p className="mt-1 text-text-secondary text-sm">
            瀏覽並了解不同風格的交易策略組合。本頁僅提供策略與風險說明，建立機器人請於「機器人管理」頁面操作。
          </p>
        </div>
        <Button variant="outline" disabled>
          <Plus className="h-4 w-4 mr-2" />
          ＋ 建立自訂策略（即將推出）
        </Button>
      </div>

      {/* 風格總覽卡片 */}
      <div className="flex flex-col" style={{ gap: '48px' }}>
        <StrategyStyleCard
          style="aggressive"
          title="激進型策略"
          subtitle="追求高波動、高報酬的進攻型策略。"
          totalBundles={aggressiveBundles.length}
          isActive={selectedStyle === 'aggressive'}
          onClick={() =>
            setSelectedStyle(
              selectedStyle === 'aggressive' ? null : 'aggressive'
            )
          }
        />
        <StrategyStyleCard
          style="balanced"
          title="平衡型策略"
          subtitle="兼顧趨勢與均值回歸的中風險策略。"
          totalBundles={balancedBundles.length}
          isActive={selectedStyle === 'balanced'}
          onClick={() =>
            setSelectedStyle(
              selectedStyle === 'balanced' ? null : 'balanced'
            )
          }
        />
        <StrategyStyleCard
          style="conservative"
          title="保守型策略"
          subtitle="以防守與長期趨勢為主，適合穩健資金。"
          totalBundles={conservativeBundles.length}
          isActive={selectedStyle === 'conservative'}
          onClick={() =>
            setSelectedStyle(
              selectedStyle === 'conservative' ? null : 'conservative'
            )
          }
        />
      </div>

      {/* 下方策略組合列表（依選取風格顯示） */}
      {selectedStyle ? (
        <StrategyBundleList
          style={selectedStyle}
          bundles={
            selectedStyle === 'aggressive'
              ? aggressiveBundles
              : selectedStyle === 'balanced'
              ? balancedBundles
              : conservativeBundles
          }
          onViewDetail={handleViewDetail}
          highlightBundleId={highlightBundleId}
        />
      ) : (
        <div className="text-left text-sm text-text-tertiary" style={{ marginTop: '44px' }}>
          請先從上方選擇一種策略風格，系統會顯示對應的策略組合。
        </div>
      )}

      {/* 詳細說明 Drawer */}
      <StrategyBundleDetailDrawer
        open={isDetailOpen && !!selectedBundle}
        bundle={selectedBundle}
        onClose={() => {
          setIsDetailOpen(false);
          setSelectedBundle(null);
        }}
      />
    </div>
  );
}
