/** 页面底部: 樱花主题 Footer(小字号, 低对比度) */
export function Footer() {
  return (
    <footer className="relative z-10 pb-7">
      {/* 与主体同步左移(lg:mr-64); 回退: 删掉 lg:mr-64 */}
      <div className="mx-auto max-w-[1440px] px-6 lg:mr-64">
        <div className="flex flex-col items-center gap-1 text-center text-[11px] text-ink/45 sm:flex-row sm:justify-center sm:gap-2">
          <span>🌸 消费者投诉文本分类系统</span>
          <span className="hidden sm:inline">·</span>
          <span>Powered by BERT</span>
          <span className="hidden sm:inline">·</span>
          <span>我们致力于更智能的消费者服务体验</span>
        </div>
      </div>
    </footer>
  );
}
