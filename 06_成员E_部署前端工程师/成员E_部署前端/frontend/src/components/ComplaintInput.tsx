import { useEffect, useRef, useState } from 'react';
import { Eraser, Sparkles } from 'lucide-react';

const EXAMPLE =
  '购买的商品存在质量问题，商家拒绝退款，客服一直推诿，联系平台也不处理。';
const MAX_LEN = 500;
const MIN_LEN = 10;

interface Props {
  value: string;
  onChange: (v: string) => void;
  onClassify: () => void;
  loading: boolean;
}

/**
 * 中央投诉输入卡片(页面视觉中心):
 * 欢迎标题 + 副标题 + 140~170px textarea + 0/500 计数器 + 清空 + ✨开始分类
 */
export function ComplaintInput({ value, onChange, onClassify, loading }: Props) {
  const [focused, setFocused] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);
  const len = value.length;
  const tooShort = len > 0 && len < MIN_LEN;
  const empty = len === 0;

  // 自动增高(限高 170px)
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 170)}px`;
  }, [value]);

  return (
    <div
      className={`glass p-6 transition-shadow sm:p-9 ${focused ? 'shadow-[var(--shadow-soft)]' : ''}`}
    >
      {/* 欢迎标题 + 副标题 */}
      <div className="mb-5 text-center">
        <h1 className="text-[22px] font-bold leading-snug text-ink sm:text-[26px]">
          🌸 欢迎使用<span className="text-grad-pink">消费者投诉文本分类系统</span>
        </h1>
        <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-ink-soft">
          请输入您想要分类的消费者投诉文本，系统将为您提供 18 类分类结果，并展示 Top3 的类别概率。
        </p>
      </div>

      {/* textarea + 计数器 */}
      <div className="relative">
        <textarea
          ref={ref}
          value={value}
          maxLength={MAX_LEN}
          placeholder="请输入消费者投诉内容..."
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="input-glass min-h-[140px] resize-none px-5 py-4 pr-16 text-[15px] leading-relaxed text-ink placeholder:text-ink-soft/55"
        />
        <span
          className={`pointer-events-none absolute right-4 bottom-3 text-xs tabular-nums ${
            len >= MAX_LEN ? 'font-semibold text-primary' : 'text-ink-soft/70'
          }`}
        >
          {len}/{MAX_LEN}
        </span>
      </div>

      {/* 辅助行: 示例 + 过短提示 */}
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => onChange(EXAMPLE)}
          className="cursor-pointer rounded-full bg-pink-light/80 px-3 py-1.5 text-xs text-primary transition hover:bg-pink-light"
          title="点击填入示例"
        >
          ✨ 试试示例
        </button>
        {tooShort && (
          <span className="text-xs text-accent-teal">
            内容过短({len}字)，请补充到 {MIN_LEN} 字以上
          </span>
        )}
      </div>

      {/* 按钮区: 清空(ghost) + 开始分类(主CTA) */}
      <div className="mt-5 flex items-center gap-3">
        <button
          type="button"
          onClick={() => onChange('')}
          disabled={empty || loading}
          className="flex h-[50px] cursor-pointer items-center gap-1.5 rounded-full px-6 text-sm font-medium text-ink-soft/80 transition hover:bg-pink-light/70 hover:text-primary disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Eraser size={16} />
          清空
        </button>
        <button
          type="button"
          onClick={onClassify}
          disabled={empty || loading}
          className="btn-grad flex-1 sm:flex-none sm:min-w-56"
        >
          <Sparkles size={18} />
          {loading ? '正在分析...' : '开始分类'}
        </button>
      </div>
    </div>
  );
}
