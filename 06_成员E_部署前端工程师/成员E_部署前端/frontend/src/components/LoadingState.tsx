import { Sparkles } from 'lucide-react';

/** Loading 状态: 花瓣 + 旋转图标 + 文案 */
export function LoadingState({ tip = 'AI 正在分析您的投诉内容' }: { tip?: string }) {
  return (
    <div className="glass fade-up flex flex-col items-center justify-center gap-4 p-12">
      <div className="relative">
        <div className="spin-slow h-14 w-14 rounded-full border-4 border-pink-light border-t-primary" />
        <span className="absolute inset-0 flex items-center justify-center text-2xl">
          🌸
        </span>
      </div>
      <div className="flex items-center gap-2 text-sm font-medium text-ink-soft">
        <Sparkles size={15} className="text-primary" />
        {tip}
      </div>
    </div>
  );
}
