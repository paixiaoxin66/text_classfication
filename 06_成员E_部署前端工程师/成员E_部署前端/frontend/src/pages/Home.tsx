import { useCallback, useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, RotateCcw } from 'lucide-react';
import { classifyText } from '../api/classification';
import { ComplaintInput } from '../components/ComplaintInput';
import { LoadingState } from '../components/LoadingState';
import { ProbabilityList } from '../components/ProbabilityList';
import { Top3Result } from '../components/Top3Result';
import { ClassificationError } from '../types/classification';
import type { ClassificationResponse } from '../types/classification';
import type { HistoryItem } from '../types/classification';

function saveHistory(item: Omit<HistoryItem, 'id' | 'timestamp'>) {
  try {
    const list: HistoryItem[] = JSON.parse(localStorage.getItem('history') ?? '[]');
    list.unshift({ ...item, id: `${Date.now()}`, timestamp: Date.now() });
    localStorage.setItem('history', JSON.stringify(list.slice(0, 50)));
  } catch {
    /* localStorage 不可用时忽略 */
  }
}

type Phase = 'idle' | 'loading' | 'done' | 'error';

export function Home() {
  const [text, setText] = useState('');
  const [phase, setPhase] = useState<Phase>('idle');
  const [result, setResult] = useState<ClassificationResponse | null>(null);
  const [error, setError] = useState<ClassificationError | null>(null);
  const [showAll, setShowAll] = useState(false);

  const handleClassify = useCallback(async () => {
    setPhase('loading');
    setError(null);
    try {
      const res = await classifyText(text);
      setResult(res);
      setShowAll(false);
      setPhase('done');
      saveHistory({
        text: res.text,
        topLabel: res.predictions[0]?.label ?? '-',
        topProbability: res.predictions[0]?.probability ?? 0,
      });
    } catch (e) {
      setError(e instanceof ClassificationError ? e : new ClassificationError('unknown', String(e)));
      setPhase('error');
    }
  }, [text]);

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      {/* 中央投诉输入卡片(欢迎标题在卡片内) */}
      <ComplaintInput
        value={text}
        onChange={setText}
        onClassify={handleClassify}
        loading={phase === 'loading'}
      />

      {/* Loading */}
      {phase === 'loading' && <LoadingState />}

      {/* 错误卡片 */}
      {phase === 'error' && error && (
        <div className="glass fade-up p-6 text-center">
          <div className="text-3xl">🌸</div>
          <div className="mt-1 text-base font-semibold text-ink">分类失败</div>
          <p className="mt-1 text-sm text-ink-soft">{error.message}</p>
          <button
            type="button"
            onClick={handleClassify}
            className="btn-grad btn-grad--md mt-4 cursor-pointer"
          >
            <RotateCcw size={15} />
            重新尝试
          </button>
        </div>
      )}

      {/* 分类结果 */}
      {phase === 'done' && result && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 px-1">
            <h2 className="flex items-center gap-2 text-lg font-bold text-ink">
              📊 分类结果
              {result.isMock && (
                <span className="rounded-full bg-accent-purple/15 px-2.5 py-0.5 text-[11px] font-semibold text-accent-purple">
                  演示数据
                </span>
              )}
            </h2>
            <span className="text-xs text-ink-soft">
              基于 BERT 模型 · 18 类分类{result.model ? ` · ${result.model}` : ''}
            </span>
          </div>

          {/* Top3(堆叠三色卡片) */}
          <Top3Result predictions={result.predictions} />

          {/* 查看全部 18 类 */}
          <div className="glass p-5">
            <button
              type="button"
              onClick={() => setShowAll((v) => !v)}
              className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-2xl py-2 text-sm font-medium text-primary transition hover:bg-pink-light/60"
            >
              {showAll ? (
                <>
                  <ChevronUp size={16} /> 收起全部 18 类
                </>
              ) : (
                <>
                  <ChevronDown size={16} /> 查看全部 18 类
                </>
              )}
            </button>
            {showAll && (
              <div className="fade-in mt-2">
                <ProbabilityList predictions={result.predictions} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* 空状态提示 */}
      {phase === 'idle' && (
        <div className="glass flex items-center gap-3 p-4 text-sm text-ink-soft">
          <AlertTriangle size={16} className="shrink-0 text-accent-teal" />
          输入投诉内容（10~500 字）后点击「开始分类」，即可获得 Top3 分类结果。
        </div>
      )}
    </div>
  );
}
