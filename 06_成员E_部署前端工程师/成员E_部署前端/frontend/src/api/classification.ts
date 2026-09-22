import { ClassificationError } from '../types/classification';
import type {
  ClassificationResponse,
  Prediction,
} from '../types/classification';

/**
 * 分类 API 统一入口
 * - 真实后端: POST {VITE_API_BASE_URL}/api/v1/classify
 * - 演示模式: VITE_USE_MOCK=true 或后端不可用时返回演示数据(明确标注, 非真实预测)
 * 以后切换真实后端, 只需要改这里与 .env, UI 层无需改动
 */

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000';
const USE_MOCK = (import.meta.env.VITE_USE_MOCK as string | undefined) === 'true';

function normText(text: string): string {
  return text.replace(/\s+/g, ' ').trim();
}

/** 演示数据 —— 仅用于后端未启动时预览 UI, 明确标注 isMock */
function mockResult(text: string): ClassificationResponse {
  const demo: Prediction[] = [
    { label: '电商平台', probability: 0.684 },
    { label: '物流快递', probability: 0.187 },
    { label: '旅游出行', probability: 0.079 },
    { label: '金融支付', probability: 0.021 },
    { label: '教育', probability: 0.011 },
    { label: '本地生活', probability: 0.006 },
    { label: '数码3C', probability: 0.004 },
    { label: '通讯运营商', probability: 0.003 },
    { label: '汽车', probability: 0.002 },
    { label: '共享出行', probability: 0.001 },
  ];
  const rest: Prediction[] = [
    '游戏', '服饰鞋包', '家居日用', '影音娱乐', '医疗健康',
    '婚恋交友', '房产家装', '母婴食品',
  ].map((label) => ({ label, probability: 0.0001 }));
  const predictions = [...demo, ...rest].sort((a, b) => b.probability - a.probability);
  return { text, predictions, model: 'mock-demo', isMock: true };
}

/**
 * 分类主入口
 * @throws ClassificationError
 */
export async function classifyText(rawText: string): Promise<ClassificationResponse> {
  const text = normText(rawText);
  if (!text) {
    throw new ClassificationError('empty', '投诉内容不能为空');
  }
  if (text.length < 10) {
    throw new ClassificationError(
      'too-short',
      `投诉内容过短(${text.length}字), 请补充到 10 字以上`,
    );
  }
  if (text.length > 500) {
    throw new ClassificationError(
      'too-long',
      `投诉内容超过 500 字上限(${text.length}字)`,
    );
  }

  // 演示模式: 直接返回演示数据
  if (USE_MOCK) {
    return mockResult(text);
  }

  // 真实请求
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/v1/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
      signal: AbortSignal.timeout(30000),
    });
  } catch {
    // 后端未启动/网络失败
    throw new ClassificationError(
      'network',
      '暂时无法连接分类服务，请检查后端服务是否启动。',
    );
  }

  if (!res.ok) {
    throw new ClassificationError(
      'server',
      `分类服务返回错误(${res.status})`,
    );
  }

  let data: unknown;
  try {
    data = await res.json();
  } catch {
    throw new ClassificationError('format', '服务返回数据无法解析');
  }

  const parsed = parseResponse(data);
  if (!parsed) {
    throw new ClassificationError('format', '服务返回数据格式异常');
  }
  return parsed;
}

/** 解析并校验后端 JSON, 保证格式正确才使用 */
function parseResponse(data: unknown): ClassificationResponse | null {
  if (typeof data !== 'object' || data === null) return null;
  const obj = data as Record<string, unknown>;
  if (typeof obj.text !== 'string') return null;
  if (!Array.isArray(obj.predictions) || obj.predictions.length === 0) return null;

  const predictions: Prediction[] = [];
  for (const item of obj.predictions) {
    if (typeof item !== 'object' || item === null) continue;
    const p = item as Record<string, unknown>;
    if (typeof p.label !== 'string') continue;
    const prob = typeof p.probability === 'number' ? p.probability : Number(p.score);
    if (!Number.isFinite(prob) || prob < 0) continue;
    predictions.push({ label: p.label, probability: prob });
  }
  if (predictions.length === 0) return null;

  predictions.sort((a, b) => b.probability - a.probability);
  return {
    text: obj.text,
    predictions,
    model: typeof obj.model === 'string' ? obj.model : undefined,
    isMock: obj.isMock === true,
  };
}
