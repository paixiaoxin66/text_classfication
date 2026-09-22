import { useMemo } from 'react';

/**
 * 樱花飘落效果
 * - CSS animation 驱动, 少量 DOM 元素, 性能友好
 * - 大小/透明度/左右摆动/时长随机, 循环飘落
 * - pointer-events: none, 不影响操作
 */

interface Petal {
  left: number;
  size: number;
  opacity: number;
  sway: number;
  duration: number;
  delay: number;
}

function randomPetal(seed: number): Petal {
  // 简单的确定性伪随机, 避免刷新时全部重排
  const r = (n: number) => {
    const x = Math.sin(seed * 999 + n * 137.5) * 10000;
    return x - Math.floor(x);
  };
  return {
    left: r(1) * 100,
    size: 8 + r(2) * 10,
    opacity: 0.35 + r(3) * 0.5,
    sway: 20 + r(4) * 50,
    duration: 9 + r(5) * 10,
    delay: -r(6) * 14,
  };
}

export function SakuraEffect({ count = 18 }: { count?: number }) {
  const petals = useMemo(
    () => Array.from({ length: count }, (_, i) => randomPetal(i + 1)),
    [count],
  );

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {petals.map((p, i) => (
        <span
          key={i}
          className="sakura-petal"
          style={{
            left: `${p.left}%`,
            width: p.size,
            height: p.size * 0.9,
            ['--petal-opacity' as string]: p.opacity,
            ['--sway' as string]: `${p.sway}px`,
            animationDuration: `${p.duration}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
}
