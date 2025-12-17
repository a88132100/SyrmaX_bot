/**
 * 策略組合列表元件
 * 
 * 在選定風格後，渲染該風格底下所有的策略組合卡片
 */

import React from "react";
import type { StrategyStyle } from "./StrategyStyleCard";
import type { StrategyBundleTemplate } from "./types";
import { StrategyBundleCard } from "./StrategyBundleCard";

type StrategyBundleListProps = {
  style: StrategyStyle;
  bundles: StrategyBundleTemplate[];
  onViewDetail: (bundle: StrategyBundleTemplate) => void;
  highlightBundleId?: string | null;
};

export function StrategyBundleList({
  style,
  bundles,
  onViewDetail,
  highlightBundleId,
}: StrategyBundleListProps) {
  const titleMap: Record<StrategyStyle, string> = {
    aggressive: "激進型策略組合",
    balanced: "平衡型策略組合",
    conservative: "保守型策略組合",
  };

  const descriptionMap: Record<StrategyStyle, string> = {
    aggressive: "適合願意承擔較大波動、追求成長的進取型使用者。",
    balanced: "在風險與報酬之間取得平衡，同時利用趨勢與均值回歸。",
    conservative: "強調資金防守與穩定性，偏重長週期與風險控管。",
  };

  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-base font-semibold text-text-primary">
          {titleMap[style]}
        </h2>
        <p className="mt-1 text-xs text-text-secondary">
          {descriptionMap[style]}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {bundles.map((bundle) => (
          <StrategyBundleCard
            key={bundle.id}
            bundle={bundle}
            onViewDetail={() => onViewDetail(bundle)}
            highlightBundleId={highlightBundleId}
          />
        ))}
      </div>
    </section>
  );
}

