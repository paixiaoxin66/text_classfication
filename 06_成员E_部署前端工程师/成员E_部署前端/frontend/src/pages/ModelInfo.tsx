import { ArrowDown, Brain, Cpu, Layers, TextCursorInput } from 'lucide-react';
import { MODEL_METRICS } from '../config/modelMetrics';

/** 模型介绍页: BERT 流程 + 常见方案对比(真实指标) */
const PIPELINE = [
  { icon: TextCursorInput, title: '文本输入', desc: '用户投诉原文' },
  { icon: Layers, title: 'Tokenizer', desc: 'BERT 子词切分 + 注意力掩码' },
  { icon: Brain, title: 'BERT', desc: 'bert-base-chinese 12 层 Transformer' },
  { icon: Cpu, title: '分类头', desc: 'Linear → 18 类 logits → Softmax' },
];

/** 常见分类方案定性对比(无虚假性能指标) */
const SCHEMES = [
  {
    name: 'TF-IDF + 朴素贝叶斯',
    type: '传统机器学习',
    desc: '基于词频统计的概率模型, 简单快速, 适合原型验证',
    suited: '小规模、可解释性要求高的场景',
  },
  {
    name: 'TF-IDF + 线性SVM',
    type: '传统机器学习',
    desc: '最大间隔分类器, 在稀疏高维特征上表现优异',
    suited: '中小规模文本分类的强基线',
  },
  {
    name: 'BERT 微调',
    type: '预训练+微调',
    desc: '利用大规模预训练语义, 对领域任务微调, 效果最佳',
    suited: '本项目最终采用(准确率 85.4%)',
  },
];

export function ModelInfo() {
  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div className="fade-up text-center">
        <h1 className="text-2xl font-bold text-ink">🧠 模型介绍</h1>
        <p className="mt-1 text-sm text-ink-soft">中文消费者投诉文本分类 · 基于 BERT 微调</p>
      </div>

      {/* 处理流程 */}
      <div className="glass p-6">
        <h3 className="mb-5 text-base font-semibold text-ink">🔁 分类处理流程</h3>
        <div className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-center">
          {PIPELINE.map((step, i) => (
            <div key={step.title} className="flex flex-1 flex-col items-center gap-2 sm:flex-row">
              <div className="flex w-full flex-col items-center rounded-2xl bg-pink-light/50 px-3 py-3 text-center">
                <step.icon size={20} className="text-primary" />
                <div className="mt-1 text-xs font-semibold text-ink">{step.title}</div>
                <div className="text-[10px] leading-tight text-ink-soft">{step.desc}</div>
              </div>
              {i < PIPELINE.length - 1 && (
                <ArrowDown size={16} className="rotate-90 shrink-0 text-primary sm:rotate-0" />
              )}
            </div>
          ))}
        </div>
        <div className="mt-4 text-center text-xs text-ink-soft">
          输出：18 类概率分布 → 取 Top3 展示
        </div>
      </div>

      {/* 真实实验指标 */}
      <div className="glass p-6">
        <h3 className="mb-4 text-base font-semibold text-ink">📈 本项目真实实验指标（同一真实测试集）</h3>
        <div className="overflow-x-auto">
          <table className="w-full min-w-130 text-left text-sm">
            <thead>
              <tr className="border-b border-pink-light text-xs text-ink-soft">
                <th className="py-2 pr-3">模型</th>
                <th className="py-2 pr-3">类型</th>
                <th className="py-2 pr-3">准确率</th>
                <th className="py-2 pr-3">Macro-F1</th>
                <th className="py-2">说明</th>
              </tr>
            </thead>
            <tbody>
              {MODEL_METRICS.map((m) => (
                <tr
                  key={m.id}
                  className={`border-b border-pink-light/40 ${m.id === 'bert' ? 'bg-pink-light/40' : ''}`}
                >
                  <td className="py-2 pr-3 font-semibold text-ink">{m.name}</td>
                  <td className="py-2 pr-3 text-xs text-ink-soft">{m.kind}</td>
                  <td className="py-2 pr-3 tabular-nums">{m.accuracy.toFixed(2)}%</td>
                  <td className="py-2 pr-3 tabular-nums">{m.macroF1.toFixed(2)}%</td>
                  <td className="py-2 text-xs text-ink-soft">{m.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 常见方案对比(定性) */}
      <div className="glass p-6">
        <h3 className="mb-4 text-base font-semibold text-ink">⚖️ 常见分类方案对比</h3>
        <div className="grid gap-3 sm:grid-cols-3">
          {SCHEMES.map((s) => (
            <div key={s.name} className="rounded-2xl bg-white/50 p-4">
              <div className="text-sm font-semibold text-ink">{s.name}</div>
              <div className="mt-0.5 text-[11px] font-medium text-primary">{s.type}</div>
              <p className="mt-1.5 text-xs leading-relaxed text-ink-soft">{s.desc}</p>
              <p className="mt-1.5 text-[11px] text-accent-teal">适用：{s.suited}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
