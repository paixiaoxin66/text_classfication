import { useState } from 'react';
import type { PageId } from './types/classification';
import { SakuraEffect } from './components/SakuraEffect';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Footer } from './components/Footer';
import { Home } from './pages/Home';
import { Statistics } from './pages/Statistics';
import { Categories } from './pages/Categories';
import { ModelInfo } from './pages/ModelInfo';
import { History } from './pages/History';

export default function App() {
  const [page, setPage] = useState<PageId>('home');

  return (
    <div className="relative min-h-screen">
      {/* 背景场景层: 参考图(右侧少女+樱花) + 左侧可读性遮罩 */}
      <div className="bg-scene" aria-hidden>
        <img src="/assets/images/background.jpg" alt="" />
        <div className="veil" />
      </div>

      {/* 樱花飘落 */}
      <SakuraEffect />

      {/* 顶栏 */}
      <Header />

      {/* 内容列: mx-auto 居中; lg 起加固定右margin → 主体整体左移, 避免输入卡遮住右侧背景人物
          回退: 删掉 lg:mr-64 即恢复原来完全居中 (原: max-w-[1440px] mx-auto 居中) */}
      <div className="relative z-10 mx-auto flex max-w-[1440px] gap-5 px-4 pt-6 pb-10 sm:px-6 lg:mr-64">
        {/* 侧边栏 */}
        <Sidebar current={page} onNavigate={setPage} />

        {/* 主内容区 */}
        <main className="min-w-0 flex-1">
          <div key={page} className="fade-in">
            {page === 'home' && <Home />}
            {page === 'statistics' && <Statistics />}
            {page === 'categories' && <Categories />}
            {page === 'model' && <ModelInfo />}
            {page === 'history' && <History />}
          </div>
        </main>
      </div>

      {/* 底部 */}
      <Footer />
    </div>
  );
}
