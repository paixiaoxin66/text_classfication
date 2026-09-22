/**
 * 分类系统核心类型定义
 */

/** 单个类别预测结果 */
export interface Prediction {
  label: string;
  probability: number;
}

/** 分类 API 响应 */
export interface ClassificationResponse {
  text: string;
  predictions: Prediction[];
  /** 后端返回的模型标识, 可为空 */
  model?: string;
  /** 是否为演示(mock)数据 —— 仅 mock 模式为 true */
  isMock?: boolean;
}

/** 分类 API 错误(带可读信息) */
export class ClassificationError extends Error {
  kind: 'empty' | 'too-short' | 'too-long' | 'network' | 'server' | 'format' | 'unknown';
  constructor(kind: ClassificationError['kind'], message: string) {
    super(message);
    this.name = 'ClassificationError';
    this.kind = kind;
  }
}

/** 侧边栏页面标识 */
export type PageId = 'home' | 'statistics' | 'categories' | 'model' | 'history';

/** 类别说明 */
export interface CategoryInfo {
  id: string;
  name: string;
  emoji: string;
  description: string;
}

/** 历史记录条目 */
export interface HistoryItem {
  id: string;
  text: string;
  topLabel: string;
  topProbability: number;
  timestamp: number;
}
