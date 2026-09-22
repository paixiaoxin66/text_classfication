import { motion } from 'framer-motion';
import { CATEGORY_EMOJI, CATEGORY_DESC, MIN_DISPLAY_PROBABILITY } from '../config/categories';
import type { Prediction } from '../types/classification';

/** Top1/Top2/Top3 三色体系(规范) */
const RANK_META = [
  {
    rank: '①',
    badge: 'Top1',
    color: '#EC4F8A',
    chipBg: 'rgba(236,79,138,0.10)',
    bar: 'linear-gradient(90deg, #EC4F8A, #FF7FA8)',
  },
  {
    rank: '②',
    badge: 'Top2',
    color: '#8E6BE8',
    chipBg: 'rgba(142,107,232,0.12)',
    bar: 'linear-gradient(90deg, #8E6BE8, #B39BF5)',
  },
  {
    rank: '③',
    badge: 'Top3',
    color: '#38B7A5',
    chipBg: 'rgba(56,183,165,0.12)',
    bar: 'linear-gradient(90deg, #38B7A5, #6FD6C6)',
  },
] as const;

interface Props {
  predictions: Prediction[];
}

/**
 * Top3 分类结果卡片(堆叠行):
 * ① + 图标 + 类别名 + Top 标签 .... 概率
 * 类别描述
 * 概率进度条(0→目标, 800ms)
 */
export function Top3Result({ predictions }: Props) {
  // 过滤规则: 低于阈值(30%)的类别不展示(Top2/Top3 常为 0.x%~几%, 无意义)
  // 极端情况: 全部低于阈值时, 保留 Top1 作为最可能的判断
  const visible = predictions.filter((p) => p.probability >= MIN_DISPLAY_PROBABILITY);
  const top3 = (visible.length > 0 ? visible : predictions.slice(0, 1)).slice(0, 3);
  const hiddenCount = predictions.length - top3.length;
  const maxProb = top3[0]?.probability ?? 1;

  return (
    <div className="space-y-4">
      {top3.map((p, i) => {
        const meta = RANK_META[i];
        const pct = p.probability * 100;
        return (
          <motion.div
            key={`${p.label}-${i}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.12, duration: 0.42, ease: 'easeOut' }}
            className="glass p-5 hover:-translate-y-1 transition-transform sm:px-6"
            style={{ borderRadius: 'var(--radius-item)' }}
          >
            {/* 行1: 排名 + 图标 + 名称 + Top标 ......... 概率 */}
            <div className="flex items-center gap-3">
              <span className="text-3xl leading-none" style={{ color: meta.color }}>
                {meta.rank}
              </span>
              <span className="text-2xl">{CATEGORY_EMOJI[p.label] ?? '🏷️'}</span>
              <span className="text-lg font-bold text-ink">{p.label}</span>
              <span
                className="rounded-full px-2.5 py-0.5 text-[11px] font-bold"
                style={{ background: meta.chipBg, color: meta.color }}
              >
                {meta.badge}
              </span>
              <div className="flex-1" />
              <span className="text-2xl font-bold tabular-nums text-ink">
                {pct.toFixed(1)}
                <span className="text-sm font-medium text-ink-soft">%</span>
              </span>
            </div>

            {/* 行2: 类别描述 */}
            <div className="mt-1.5 pl-14 text-xs leading-relaxed text-ink-soft sm:pl-16">
              {CATEGORY_DESC[p.label] ?? '该类别投诉'}
            </div>

            {/* 行3: 概率进度条(0→目标) */}
            <div className="mt-3 ml-14 h-2.5 w-[calc(100%-56px)] overflow-hidden rounded-full bg-pink-light/60 sm:ml-16 sm:w-[calc(100%-64px)]">
              <div
                className="progress-fill h-full rounded-full"
                style={{
                  width: `${Math.max(2, (pct / (maxProb * 100 || 1)) * 100)}%`,
                  background: meta.bar,
                }}
              />
            </div>
          </motion.div>
        );
      })}

      {/* 提示: 有类别因置信度过低被过滤 */}
      {hiddenCount > 0 && (
        <p className="px-1 text-xs text-ink-soft/70">
          💡 其余 {hiddenCount} 个类别置信度低于 {MIN_DISPLAY_PROBABILITY * 100}%，未展示（可展开「查看全部 18 类」查看）。
        </p>
      )}
    </div>
  );
}
