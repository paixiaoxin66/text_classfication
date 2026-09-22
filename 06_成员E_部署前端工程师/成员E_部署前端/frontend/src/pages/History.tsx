import { useEffect, useState } from 'react';
import { Trash2, History as HistoryIcon } from 'lucide-react';
import { CATEGORY_EMOJI } from '../config/categories';
import type { HistoryItem } from '../types/classification';

function load(): HistoryItem[] {
  try {
    return JSON.parse(localStorage.getItem('history') ?? '[]') as HistoryItem[];
  } catch {
    return [];
  }
}

/** 历史记录页: localStorage 存取, 查看/删除/清空 */
export function History() {
  const [items, setItems] = useState<HistoryItem[]>([]);

  useEffect(() => {
    setItems(load());
  }, []);

  const remove = (id: string) => {
    const next = items.filter((i) => i.id !== id);
    setItems(next);
    localStorage.setItem('history', JSON.stringify(next));
  };

  const clearAll = () => {
    setItems([]);
    localStorage.removeItem('history');
  };

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div className="fade-up flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">🕘 历史记录</h1>
          <p className="mt-1 text-sm text-ink-soft">保存在本机浏览器(localStorage)，共 {items.length} 条</p>
        </div>
        {items.length > 0 && (
          <button
            type="button"
            onClick={clearAll}
            className="glass cursor-pointer rounded-full px-4 py-2 text-xs font-medium text-ink-soft transition hover:text-primary"
          >
            清空历史
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="glass flex flex-col items-center gap-2 p-10 text-center">
          <HistoryIcon size={32} className="text-primary/50" />
          <p className="text-sm text-ink-soft">暂无历史记录</p>
          <p className="text-xs text-ink-soft/60">去首页提交一条投诉文本试试吧</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((it) => (
            <div key={it.id} className="glass group p-4 transition hover:-translate-y-0.5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="line-clamp-2 text-sm leading-relaxed text-ink">{it.text}</p>
                  <div className="mt-2 flex items-center gap-2 text-xs">
                    <span className="rounded-full bg-primary/10 px-2 py-0.5 font-semibold text-primary">
                      {CATEGORY_EMOJI[it.topLabel] ?? '🏷️'} {it.topLabel}
                    </span>
                    <span className="font-medium tabular-nums text-ink-soft">
                      {(it.topProbability * 100).toFixed(1)}%
                    </span>
                    <span className="text-ink-soft/60">
                      {new Date(it.timestamp).toLocaleString('zh-CN', { hour12: false })}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => remove(it.id)}
                  title="删除"
                  className="shrink-0 cursor-pointer rounded-full p-2 text-ink-soft/50 transition hover:bg-rose-50 hover:text-rose-500"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
