import { CATEGORY_EMOJI } from '../config/categories';
import type { Prediction } from '../types/classification';

interface Props {
  predictions: Prediction[];
}

/** 完整 18 类概率列表: 自动排序, Top3 高亮, 其余弱化 */
export function ProbabilityList({ predictions }: Props) {
  const maxProb = predictions[0]?.probability ?? 1;
  const maxPct = maxProb * 100 || 1;

  return (
    <div className="grid gap-1.5 sm:grid-cols-2">
      {predictions.map((p, idx) => {
        const pct = p.probability * 100;
        const isTop = idx < 3;
        const width = (pct / maxPct) * 100;
        return (
          <div
            key={p.label}
            className={`flex items-center gap-3 rounded-2xl px-3.5 py-2 transition-colors ${
              isTop ? 'bg-pink-light/50' : 'bg-white/35 hover:bg-white/60'
            }`}
          >
            <span
              className={`w-5 text-right text-xs font-bold tabular-nums ${
                isTop ? 'text-primary' : 'text-ink-soft/70'
              }`}
            >
              {idx + 1}
            </span>
            <span className="w-5 text-center text-base">{CATEGORY_EMOJI[p.label] ?? '🏷️'}</span>
            <span
              className={`w-24 truncate text-sm ${
                isTop ? 'font-semibold text-ink' : 'text-ink-soft/80'
              }`}
            >
              {p.label}
            </span>
            <div className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-pink-light/50">
              <div
                className={`progress-fill h-full rounded-full ${
                  isTop
                    ? 'bg-gradient-to-r from-primary to-accent-purple'
                    : 'bg-accent-teal/50'
                }`}
                style={{ width: `${Math.max(1.5, width)}%` }}
              />
            </div>
            <span className="w-12 text-right text-xs font-medium tabular-nums text-ink-soft">
              {pct.toFixed(1)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
