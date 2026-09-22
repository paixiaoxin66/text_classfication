import { useMemo, useState } from 'react';
import { DATASET_STATS, MODEL_METRICS, CURRENT_MODEL, CURRENT_ACC, CURRENT_F1 } from '../config/modelMetrics';

/**
 * 数据统计 Dashboard
 * 全部指标来自项目真实实验结果(不伪造)
 */
export function Statistics() {
  const [metric, setMetric] = useState<'accuracy' | 'macroF1'>('accuracy');
  const maxAccuracy = useMemo(() => Math.max(...MODEL_METRICS.map((m) => m.accuracy)), []);
  const maxF1 = useMemo(() => Math.max(...MODEL_METRICS.map((m) => m.macroF1)), []);

  const statCards = [
    { label: '数据集规模', value: '9,043', unit: '原始投诉', emoji: '🗂️' },
    { label: '分类类别', value: String(DATASET_STATS.classes), unit: '类', emoji: '🏷️' },
    { label: '训练集', value: DATASET_STATS.train.toLocaleString(), unit: '条(含77%增强)', emoji: '📚' },
    { label: '测试集', value: String(DATASET_STATS.test), unit: '条(100%真实)', emoji: '🧪' },
    { label: '模型', value: 'BERT', unit: CURRENT_MODEL, emoji: '🧠' },
    { label: 'Accuracy', value: `${CURRENT_ACC.toFixed(2)}%`, unit: '测试集', emoji: '🎯' },
    { label: 'Macro-F1', value: `${CURRENT_F1.toFixed(2)}%`, unit: '测试集', emoji: '📈' },
    { label: '完全重复率', value: '0.00%', unit: '训练集', emoji: '✨' },
  ];

  // 类别分布(真实数据: 18 类训练样本量)
  const distRaw: [string, number][] = [
    ['本地生活', 1872], ['电商平台', 1822], ['金融支付', 1841], ['服饰鞋包', 1813],
    ['家居日用', 1811], ['教育', 1803], ['旅游出行', 1803], ['影音娱乐', 1799],
    ['汽车', 1797], ['游戏', 1774], ['物流快递', 1768], ['通讯运营商', 1767],
    ['数码3C', 1766], ['房产家装', 1764], ['共享出行', 1783], ['婚恋交友', 1278],
    ['医疗健康', 1321], ['母婴食品', 418],
  ];
  const dist = distRaw.sort((a, b) => b[1] - a[1]);
  const maxDist = dist[0][1];

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <div className="fade-up text-center">
        <h1 className="text-2xl font-bold text-ink">📊 数据统计</h1>
        <p className="mt-1 text-sm text-ink-soft">数据集与模型实验真实指标</p>
      </div>

      {/* 指标卡 */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {statCards.map((s) => (
          <div key={s.label} className="glass p-4 text-center hover:-translate-y-0.5 transition-transform">
            <div className="text-xl">{s.emoji}</div>
            <div className="mt-1 text-xl font-bold text-ink">{s.value}</div>
            <div className="text-[11px] text-ink-soft">{s.label}</div>
            {s.unit && <div className="text-[10px] text-ink-soft/70">{s.unit}</div>}
          </div>
        ))}
      </div>

      {/* 类别分布柱状图(纯 CSS, 无图表依赖) */}
      <div className="glass p-6">
        <h3 className="mb-4 text-base font-semibold text-ink">🏷️ 18 类训练样本分布</h3>
        <div className="space-y-1.5">
          {dist.map(([name, n]) => (
            <div key={name} className="flex items-center gap-3">
              <span className="w-20 truncate text-right text-xs text-ink-soft">{name}</span>
              <div className="h-4 flex-1 overflow-hidden rounded-full bg-pink-light/50">
                <div
                  className="progress-fill h-full rounded-full bg-gradient-to-r from-primary to-accent-purple"
                  style={{ width: `${(n / maxDist) * 100}%` }}
                />
              </div>
              <span className="w-12 text-xs tabular-nums text-ink-soft">{n}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 模型对比(真实测试指标) */}
      <div className="glass p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-ink">🤖 模型效果对比（同一真实测试集）</h3>
          <div className="flex rounded-full bg-pink-light/60 p-1 text-xs">
            {(['accuracy', 'macroF1'] as const).map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => setMetric(k)}
                className={`cursor-pointer rounded-full px-3 py-1 font-medium transition ${
                  metric === k ? 'bg-white text-primary shadow' : 'text-ink-soft'
                }`}
              >
                {k === 'accuracy' ? '准确率' : 'Macro-F1'}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          {MODEL_METRICS.map((m) => {
            const val = metric === 'accuracy' ? m.accuracy : m.macroF1;
            const max = metric === 'accuracy' ? maxAccuracy : maxF1;
            return (
              <div key={m.id} className="flex items-center gap-4">
                <div className="w-32 shrink-0">
                  <div className="text-sm font-semibold text-ink">{m.name}</div>
                  <div className="text-[10px] text-ink-soft">{m.note}</div>
                </div>
                <div className="h-5 flex-1 overflow-hidden rounded-full bg-pink-light/50">
                  <div
                    className={`progress-fill h-full rounded-full ${
                      m.kind === '深度学习'
                        ? 'bg-gradient-to-r from-primary to-[#FF7FB2]'
                        : 'bg-gradient-to-r from-accent-purple to-[#A99DF8]'
                    }`}
                    style={{ width: `${(val / max) * 100}%` }}
                  />
                </div>
                <span className="w-16 text-right text-sm font-bold tabular-nums text-ink">
                  {val.toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>
        <p className="mt-4 text-[11px] text-ink-soft/70">
          数据来源：data/out_ablation/char_wb 与 data/out/bert_report.txt（seed=42，可复现）
        </p>
      </div>
    </div>
  );
}
