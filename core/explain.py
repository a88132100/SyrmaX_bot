# core/explain.py
"""
稽核層解釋生成系統
實現5種母模板和解釋生成器
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .events import ExplainCreated, EventType, SignalGenerated, RiskChecked


class ExplanationTemplate:
    """解釋模板基類"""
    
    def __init__(self, template_id: str, name: str, description: str):
        self.template_id = template_id
        self.name = name
        self.description = description
        
    def generate(self, signal: SignalGenerated, risk_result: RiskChecked, 
                context: Dict[str, Any]) -> List[str]:
        """生成解釋內容"""
        raise NotImplementedError


class TrendATRTemplate(ExplanationTemplate):
    """趨勢ATR模板"""
    
    def __init__(self):
        super().__init__(
            template_id="trend_atr_v2",
            name="趨勢追蹤ATR模板",
            description="基於ATR和趨勢指標的解釋模板"
        )
        
    def generate(self, signal: SignalGenerated, risk_result: RiskChecked, 
                context: Dict[str, Any]) -> List[str]:
        """生成趨勢ATR解釋"""
        explanations = []
        
        # 獲取指標數據
        atr = signal.indicators.get("atr", 0)
        rsi = signal.indicators.get("rsi", 50)
        ema_5 = signal.indicators.get("ema_5", 0)
        ema_20 = signal.indicators.get("ema_20", 0)
        
        # 方向判斷
        side_text = "做多" if signal.side == "long" else "做空" if signal.side == "short" else "觀望"
        
        # 1. 核心依據
        if signal.side in ["long", "short"]:
            if rsi < 30:
                trend_reason = f"RSI={rsi:.1f}顯示超賣，{side_text}信號"
            elif rsi > 70:
                trend_reason = f"RSI={rsi:.1f}顯示超買，{side_text}信號"
            else:
                trend_reason = f"RSI={rsi:.1f}處於正常區間，{side_text}信號"
                
            if ema_5 > ema_20:
                trend_reason += f"；EMA5({ema_5:.2f}) > EMA20({ema_20:.2f})確認上升趨勢"
            else:
                trend_reason += f"；EMA5({ema_5:.2f}) < EMA20({ema_20:.2f})確認下降趨勢"
                
            explanations.append(trend_reason)
            
            # 2. 風控限制
            leverage = context.get("leverage", 1.0)
            dist_to_liq = context.get("dist_to_liq_pct", 50.0)
            daily_loss = context.get("daily_loss_pct", 0.0)
            
            risk_info = f"風控狀態：槓桿{leverage}x"
            if dist_to_liq < 20:
                risk_info += f"，距爆倉{dist_to_liq:.1f}%較近"
            else:
                risk_info += f"，距爆倉{dist_to_liq:.1f}%安全"
                
            if daily_loss > 1:
                risk_info += f"，當日已虧損{daily_loss:.1f}%"
            else:
                risk_info += f"，當日虧損{daily_loss:.1f}%正常"
                
            explanations.append(risk_info)
            
            # 3. ATR分析
            if atr > 0:
                atr_pct = (atr / context.get("current_price", 1)) * 100
                if atr_pct > 2:
                    atr_analysis = f"ATR={atr:.4f}({atr_pct:.2f}%)顯示高波動，需謹慎"
                elif atr_pct < 0.5:
                    atr_analysis = f"ATR={atr:.4f}({atr_pct:.2f}%)顯示低波動，機會較好"
                else:
                    atr_analysis = f"ATR={atr:.4f}({atr_pct:.2f}%)顯示正常波動"
                explanations.append(atr_analysis)
                
            # 4. 下單方式
            order_type = context.get("order_type", "market")
            max_slippage = context.get("max_slippage_bps", 5)
            if order_type == "market":
                explanations.append(f"下單方式：市價單，滑點上限{max_slippage}bps")
            else:
                explanations.append(f"下單方式：限價單，滑點上限{max_slippage}bps")
                
        else:
            explanations.append("當前市場條件不滿足趨勢策略，維持觀望")
            
        return explanations


class RangeRevertTemplate(ExplanationTemplate):
    """區間反轉模板"""
    
    def __init__(self):
        super().__init__(
            template_id="range_revert_v1",
            name="區間反轉模板",
            description="基於區間震盪和反轉信號的解釋模板"
        )
        
    def generate(self, signal: SignalGenerated, risk_result: RiskChecked, 
                context: Dict[str, Any]) -> List[str]:
        """生成區間反轉解釋"""
        explanations = []
        
        # 獲取指標數據
        rsi = signal.indicators.get("rsi", 50)
        bb_upper = signal.indicators.get("bb_upper", 0)
        bb_lower = signal.indicators.get("bb_lower", 0)
        current_price = context.get("current_price", 0)
        
        side_text = "做多" if signal.side == "long" else "做空" if signal.side == "short" else "觀望"
        
        # 1. 區間分析
        if signal.side in ["long", "short"]:
            if bb_upper > 0 and bb_lower > 0:
                bb_width = ((bb_upper - bb_lower) / current_price) * 100
                if bb_width < 2:
                    range_analysis = f"布林通道寬度{bb_width:.2f}%顯示窄幅震盪，適合反轉策略"
                else:
                    range_analysis = f"布林通道寬度{bb_width:.2f}%顯示寬幅震盪，需謹慎"
                explanations.append(range_analysis)
                
            # 2. RSI反轉信號
            if rsi < 30:
                rsi_signal = f"RSI={rsi:.1f}顯示超賣，{side_text}反轉信號強烈"
            elif rsi > 70:
                rsi_signal = f"RSI={rsi:.1f}顯示超買，{side_text}反轉信號強烈"
            elif 40 <= rsi <= 60:
                rsi_signal = f"RSI={rsi:.1f}處於中性區間，{side_text}信號較弱"
            else:
                rsi_signal = f"RSI={rsi:.1f}顯示{side_text}反轉信號"
            explanations.append(rsi_signal)
            
            # 3. 風控狀態
            leverage = context.get("leverage", 1.0)
            explanations.append(f"風控：槓桿{leverage}x，反轉策略風險較低")
            
            # 4. 下單建議
            explanations.append("建議：反轉策略適合小倉位，設置緊密止損")
            
        else:
            explanations.append("當前不滿足區間反轉條件，維持觀望")
            
        return explanations


class BreakoutPullbackTemplate(ExplanationTemplate):
    """突破回抽模板"""
    
    def __init__(self):
        super().__init__(
            template_id="breakout_pullback",
            name="突破回抽模板",
            description="基於突破和回抽確認的解釋模板"
        )
        
    def generate(self, signal: SignalGenerated, risk_result: RiskChecked, 
                context: Dict[str, Any]) -> List[str]:
        """生成突破回抽解釋"""
        explanations = []
        
        # 獲取指標數據
        volume = signal.indicators.get("volume", 0)
        avg_volume = signal.indicators.get("avg_volume", 0)
        price_change = signal.indicators.get("price_change_pct", 0)
        
        side_text = "做多" if signal.side == "long" else "做空" if signal.side == "short" else "觀望"
        
        if signal.side in ["long", "short"]:
            # 1. 突破確認
            if volume > avg_volume * 1.5:
                volume_analysis = f"成交量{volume:.0f}超過平均{avg_volume:.0f}的1.5倍，突破確認"
            else:
                volume_analysis = f"成交量{volume:.0f}未達突破標準，需謹慎"
            explanations.append(volume_analysis)
            
            # 2. 價格動量
            if abs(price_change) > 2:
                momentum_analysis = f"價格變化{price_change:.2f}%顯示強勁動量，{side_text}信號可靠"
            else:
                momentum_analysis = f"價格變化{price_change:.2f}%動量不足，{side_text}信號較弱"
            explanations.append(momentum_analysis)
            
            # 3. 風控建議
            explanations.append("風控：突破策略需設置追蹤止損，避免假突破")
            
            # 4. 下單方式
            explanations.append("建議：突破確認後立即進場，設置合理止損")
            
        else:
            explanations.append("當前無明顯突破信號，維持觀望")
            
        return explanations


class MomentumVolumeTemplate(ExplanationTemplate):
    """動量量能模板"""
    
    def __init__(self):
        super().__init__(
            template_id="momentum_volume",
            name="動量量能模板",
            description="基於動量指標和成交量分析的解釋模板"
        )
        
    def generate(self, signal: SignalGenerated, risk_result: RiskChecked, 
                context: Dict[str, Any]) -> List[str]:
        """生成動量量能解釋"""
        explanations = []
        
        # 獲取指標數據
        macd = signal.indicators.get("macd", 0)
        macd_signal = signal.indicators.get("macd_signal", 0)
        volume_ratio = signal.indicators.get("volume_ratio", 1.0)
        
        side_text = "做多" if signal.side == "long" else "做空" if signal.side == "short" else "觀望"
        
        if signal.side in ["long", "short"]:
            # 1. MACD動量
            if macd > macd_signal:
                macd_analysis = f"MACD({macd:.4f}) > 信號線({macd_signal:.4f})，{side_text}動量強勁"
            else:
                macd_analysis = f"MACD({macd:.4f}) < 信號線({macd_signal:.4f})，{side_text}動量不足"
            explanations.append(macd_analysis)
            
            # 2. 成交量確認
            if volume_ratio > 1.2:
                volume_analysis = f"成交量比率{volume_ratio:.2f}顯示資金流入，{side_text}信號確認"
            else:
                volume_analysis = f"成交量比率{volume_ratio:.2f}顯示資金不足，{side_text}信號較弱"
            explanations.append(volume_analysis)
            
            # 3. 風控建議
            explanations.append("風控：動量策略需快速進出，避免滯留")
            
            # 4. 下單建議
            explanations.append("建議：動量策略適合短線操作，設置緊密止損")
            
        else:
            explanations.append("當前動量不足，維持觀望")
            
        return explanations


class MeanReversionTemplate(ExplanationTemplate):
    """均值回歸模板"""
    
    def __init__(self):
        super().__init__(
            template_id="mean_reversion",
            name="均值回歸模板",
            description="基於均值回歸理論的解釋模板"
        )
        
    def generate(self, signal: SignalGenerated, risk_result: RiskChecked, 
                context: Dict[str, Any]) -> List[str]:
        """生成均值回歸解釋"""
        explanations = []
        
        # 獲取指標數據
        rsi = signal.indicators.get("rsi", 50)
        bb_position = signal.indicators.get("bb_position", 0.5)
        price_deviation = signal.indicators.get("price_deviation", 0)
        
        side_text = "做多" if signal.side == "long" else "做空" if signal.side == "short" else "觀望"
        
        if signal.side in ["long", "short"]:
            # 1. 偏離度分析
            if abs(price_deviation) > 2:
                deviation_analysis = f"價格偏離均值{price_deviation:.2f}%，{side_text}回歸信號強烈"
            else:
                deviation_analysis = f"價格偏離均值{price_deviation:.2f}%，{side_text}回歸信號較弱"
            explanations.append(deviation_analysis)
            
            # 2. 布林通道位置
            if bb_position < 0.2:
                bb_analysis = f"價格位於布林通道下軌附近，{side_text}回歸機會"
            elif bb_position > 0.8:
                bb_analysis = f"價格位於布林通道上軌附近，{side_text}回歸機會"
            else:
                bb_analysis = f"價格位於布林通道中部，{side_text}回歸信號一般"
            explanations.append(bb_analysis)
            
            # 3. RSI確認
            if (side_text == "做多" and rsi < 40) or (side_text == "做空" and rsi > 60):
                rsi_analysis = f"RSI={rsi:.1f}確認{side_text}回歸信號"
            else:
                rsi_analysis = f"RSI={rsi:.1f}對{side_text}回歸信號支持不足"
            explanations.append(rsi_analysis)
            
            # 4. 風控建議
            explanations.append("風控：均值回歸策略需耐心等待，設置寬鬆止損")
            
        else:
            explanations.append("當前價格接近均值，無回歸信號")
            
        return explanations


class ExplanationGenerator:
    """解釋生成器"""
    
    def __init__(self):
        self.templates: Dict[str, ExplanationTemplate] = {}
        self._setup_templates()
        
    def _setup_templates(self):
        """設置解釋模板"""
        self.templates["trend_atr_v2"] = TrendATRTemplate()
        self.templates["range_revert_v1"] = RangeRevertTemplate()
        self.templates["breakout_pullback"] = BreakoutPullbackTemplate()
        self.templates["momentum_volume"] = MomentumVolumeTemplate()
        self.templates["mean_reversion"] = MeanReversionTemplate()
        
    def generate_explanation(self, signal: SignalGenerated, risk_result: RiskChecked, 
                           context: Dict[str, Any], template_id: str = None) -> ExplainCreated:
        """生成解釋"""
        try:
            # 自動選擇模板
            if not template_id:
                template_id = self._select_template(signal, context)
                
            template = self.templates.get(template_id)
            if not template:
                template = self.templates["trend_atr_v2"]  # 預設模板
                
            # 生成解釋內容
            explanations = template.generate(signal, risk_result, context)
            
            # 計算解釋品質
            quality = self._assess_quality(explanations)
            confidence = self._calculate_confidence(signal, risk_result, context)
            
            # 創建解釋事件
            explain_event = ExplainCreated(
                event_type=EventType.EXPLAIN_CREATED,
                account_id=signal.account_id,
                venue=signal.venue,
                symbol=signal.symbol,
                strategy_id=signal.strategy_id,
                idempotency_key=signal.idempotency_key,
                explanation=explanations,
                template_used=template_id,
                explanation_quality=quality,
                word_count=sum(len(exp) for exp in explanations),
                confidence_score=confidence
            )
            
            return explain_event
            
        except Exception as e:
            logging.error(f"生成解釋時發生錯誤: {e}")
            # 返回預設解釋
            return ExplainCreated(
                event_type=EventType.EXPLAIN_CREATED,
                account_id=signal.account_id,
                venue=signal.venue,
                symbol=signal.symbol,
                strategy_id=signal.strategy_id,
                idempotency_key=signal.idempotency_key,
                explanation=["系統無法生成詳細解釋，請檢查信號數據"],
                template_used="default",
                explanation_quality="LOW",
                word_count=20,
                confidence_score=0.1
            )
            
    def _select_template(self, signal: SignalGenerated, context: Dict[str, Any]) -> str:
        """自動選擇解釋模板"""
        # 基於策略ID選擇模板
        strategy_id = signal.strategy_id.lower()
        
        if "trend" in strategy_id or "ema" in strategy_id:
            return "trend_atr_v2"
        elif "range" in strategy_id or "revert" in strategy_id:
            return "range_revert_v1"
        elif "breakout" in strategy_id or "break" in strategy_id:
            return "breakout_pullback"
        elif "momentum" in strategy_id or "volume" in strategy_id:
            return "momentum_volume"
        elif "mean" in strategy_id or "reversion" in strategy_id:
            return "mean_reversion"
        else:
            return "trend_atr_v2"  # 預設模板
            
    def _assess_quality(self, explanations: List[str]) -> str:
        """評估解釋品質"""
        if not explanations:
            return "LOW"
            
        total_words = sum(len(exp) for exp in explanations)
        if total_words < 50:
            return "LOW"
        elif total_words < 100:
            return "NORMAL"
        else:
            return "HIGH"
            
    def _calculate_confidence(self, signal: SignalGenerated, risk_result: RiskChecked, 
                            context: Dict[str, Any]) -> float:
        """計算解釋信心度"""
        confidence = 0.5  # 基礎信心度
        
        # 基於信號強度調整
        if hasattr(signal, 'signal_strength'):
            confidence += signal.signal_strength * 0.3
            
        # 基於風控結果調整
        if hasattr(risk_result, 'passed') and risk_result.passed:
            confidence += 0.2
        elif hasattr(risk_result, 'passed') and not risk_result.passed:
            confidence -= 0.1
            
        # 基於指標完整性調整
        indicator_count = len(signal.indicators)
        if indicator_count > 5:
            confidence += 0.1
        elif indicator_count < 3:
            confidence -= 0.1
            
        return max(0.0, min(1.0, confidence))
