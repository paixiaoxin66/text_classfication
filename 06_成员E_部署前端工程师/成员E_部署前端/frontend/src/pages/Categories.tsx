import { CATEGORIES } from '../config/categories';

/** 分类说明页: 18 个类别卡片 */
export function Categories() {
  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <div className="fade-up text-center">
        <h1 className="text-2xl font-bold text-ink">🏷️ 分类说明</h1>
        <p className="mt-1 text-sm text-ink-soft">
          共 {CATEGORIES.length} 个投诉类别（与项目真实标签一致）
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {CATEGORIES.map((c, i) => (
          <div
            key={c.id}
            className="glass fade-up p-4 hover:-translate-y-1 transition-transform"
            style={{ animationDelay: `${Math.min(i * 30, 400)}ms` }}
          >
            <div className="flex items-center gap-2">
              <span className="text-2xl">{c.emoji}</span>
              <span className="font-semibold text-ink">{c.name}</span>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-ink-soft">{c.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
