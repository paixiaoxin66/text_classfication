import { Sparkles } from 'lucide-react';

/** 顶部 Header: Logo + 系统名(中文粗/英文淡) + Slogan + 模型状态/AI助手/头像 */
export function Header() {
  return (
    <header className="relative z-20 sticky top-0">
      {/* 与主体同步左移(lg:mr-64), 保持与内容列对齐; 回退: 删掉 lg:mr-64 */}
      <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:mr-64">
        {/* 左: Logo + 系统名 */}
        <div className="flex items-center gap-3">
          <div className="glass flex h-12 w-12 items-center justify-center text-2xl shadow-[var(--shadow-soft)]">
            🌸
          </div>
          <div className="leading-tight">
            <div className="text-xl font-bold text-ink sm:text-[21px]">
              消费者投诉文本分类系统
            </div>
            <div className="text-[11px] tracking-[0.08em] text-ink opacity-[0.55]">
              Consumer Complaint Classification
            </div>
          </div>
        </div>

        {/* 中: 品牌 Slogan */}
        <div className="hidden items-center gap-2 lg:flex">
          <span className="text-sm text-ink/60 italic">「让每一条投诉，都有合适的归属。」</span>
        </div>

        {/* 右: 模型状态 + AI助手 + 头像 */}
        <div className="flex items-center gap-2.5">
          <div className="glass hidden items-center gap-2 rounded-full px-3.5 py-2 text-xs font-medium text-ink/70 sm:flex">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            模型已就绪
          </div>
          <button
            type="button"
            className="btn-grad btn-grad--sm hidden cursor-pointer items-center gap-1.5 sm:inline-flex"
          >
            <Sparkles size={15} />
            AI 小助手
          </button>
          <div
            title="AI 助手头像"
            className="glass h-11 w-11 cursor-pointer p-0.5"
          >
            <img
              src="/assets/images/anime-girl.png"
              alt="助手头像"
              className="h-full w-full rounded-full object-cover"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).src = '/assets/images/anime-girl.svg';
              }}
            />
          </div>
        </div>
      </div>
    </header>
  );
}
