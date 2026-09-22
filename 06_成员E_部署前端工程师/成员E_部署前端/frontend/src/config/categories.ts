import type { CategoryInfo } from '../types/classification';

/**
 * 18 个投诉类别(与项目真实标签一致, 来自黑猫投诉行业分类)
 * 如需调整, 只改这里即可, 前端不写死分类逻辑
 */
export const CATEGORIES: CategoryInfo[] = [
  { id: 'education', name: '教育', emoji: '📚', description: '涉及培训机构、课程消费、退费纠纷等投诉' },
  { id: 'ecommerce', name: '电商平台', emoji: '🛍️', description: '涉及商品购买、退换货、商家服务等投诉' },
  { id: 'finance', name: '金融支付', emoji: '💳', description: '涉及网贷、信用卡、支付平台等投诉' },
  { id: 'logistics', name: '物流快递', emoji: '📦', description: '涉及运输时效、快递丢件、物流信息等投诉' },
  { id: 'telecom', name: '通讯运营商', emoji: '📱', description: '涉及话费、宽带、套餐等通信服务投诉' },
  { id: 'digital3c', name: '数码3C', emoji: '💻', description: '涉及手机、电脑、数码产品等投诉' },
  { id: 'automobile', name: '汽车', emoji: '🚗', description: '涉及汽车销售、维修、租赁等投诉' },
  { id: 'travel', name: '旅游出行', emoji: '✈️', description: '涉及机票、酒店、旅行社等投诉' },
  { id: 'rideshare', name: '共享出行', emoji: '🚕', description: '涉及网约车、共享单车等出行服务投诉' },
  { id: 'local-life', name: '本地生活', emoji: '🍜', description: '涉及餐饮、外卖、美容美发等本地服务投诉' },
  { id: 'fashion', name: '服饰鞋包', emoji: '👗', description: '涉及服装、鞋包质量与售后投诉' },
  { id: 'home-goods', name: '家居日用', emoji: '🛋️', description: '涉及家具、日用品质量问题投诉' },
  { id: 'gaming', name: '游戏', emoji: '🎮', description: '涉及游戏充值、账号、防沉迷等投诉' },
  { id: 'entertainment', name: '影音娱乐', emoji: '🎬', description: '涉及视频、音乐、直播等娱乐平台投诉' },
  { id: 'medical', name: '医疗健康', emoji: '🏥', description: '涉及医疗美容、体检、药品等健康投诉' },
  { id: 'dating', name: '婚恋交友', emoji: '💌', description: '涉及婚恋平台、交友服务投诉' },
  { id: 'realestate', name: '房产家装', emoji: '🏠', description: '涉及房产中介、装修服务投诉' },
  { id: 'baby-food', name: '母婴食品', emoji: '🍼', description: '涉及母婴用品、食品质量投诉' },
];

/** 类别名 -> 说明 的快速查找表 */
export const CATEGORY_DESC: Record<string, string> = Object.fromEntries(
  CATEGORIES.map((c) => [c.name, c.description]),
);

/** 类别名 -> emoji */
export const CATEGORY_EMOJI: Record<string, string> = Object.fromEntries(
  CATEGORIES.map((c) => [c.name, c.emoji]),
);

/**
 * Top3 展示的最低置信度阈值:
 * 概率低于该值的类别不展示(模型高置信时 Top2/Top3 常为 0.x%, 展示无意义)
 */
export const MIN_DISPLAY_PROBABILITY = 0.3;
