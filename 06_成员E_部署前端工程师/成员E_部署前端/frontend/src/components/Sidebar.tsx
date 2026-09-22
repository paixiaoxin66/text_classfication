import { BarChart3, CircleHelp, Cpu, Home as HomeIcon, History } from 'lucide-react';
import type { PageId } from '../types/classification';

const MENUS: { id: PageId; label: string; icon: typeof HomeIcon }[] = [
  { id: 'home', label: '首页', icon: HomeIcon },
  { id: 'statistics', label: '数据统计', icon: BarChart3 },
  { id: 'categories', label: '分类说明', icon: CircleHelp },
  { id: 'model', label: '模型介绍', icon: Cpu },
  { id: 'history', label: '历史记录', icon: History },
];

interface Props {
  current: PageId;
  onNavigate: (page: PageId) => void;
}

/** 左侧 Sidebar: 白/半透明玻璃, 选中项粉→紫渐变胶囊 */
export function Sidebar({ current, onNavigate }: Props) {
  return (
    <aside className="sticky top-20 z-10 hidden h-fit w-56 shrink-0 md:block">
      <nav
        className="flex flex-col gap-2 p-3"
        style={{
          background: 'rgba(255,255,255,0.65)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.8)',
          borderRadius: 28,
          boxShadow: '0 20px 60px -18px rgba(244,91,149,0.25)',
        }}
      >
        {MENUS.map((item) => {
          const active = current === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={[
                'flex cursor-pointer items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all',
                active
                  ? 'text-white shadow-[0_10px_24px_-8px_rgba(244,91,149,0.6)]'
                  : 'text-[#2E2945]/75 hover:bg-[#FFE4EF]/80 hover:text-primary',
              ].join(' ')}
              style={
                active
                  ? {
                      background: 'linear-gradient(90deg, #ff72ad 0%, #b985f5 100%)',
                    }
                  : undefined
              }
            >
              <Icon size={18} strokeWidth={active ? 2.4 : 2} />
              {item.label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
