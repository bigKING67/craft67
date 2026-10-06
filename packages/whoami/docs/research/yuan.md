# Yuan：输入与交付值得吸收，规则分数不当真值

来源：[README-CN](https://github.com/shizhilya/yuan/blob/main/README-CN.md)、references/bazi/bazi_skill_engine.py、references/ziwei/references/DOMAIN_MODEL.md。精确源版本见 manifest。GitHub API 未识别仓库 license；这不是对作者权利的结论，本次不复制其实现或提示词。

OBSERVED：Yuan 用统一出生资料组织六个体系，区分能运行、受限与阻塞能力。默认成品结构覆盖结论、事业、财富、关系和五年窗口；另强调事实和解读分层。八字 Python 参考实现依赖 swisseph，包含太阳黄经节气判断及本地 23:00 换日；其强弱比值、藏干权重、月令加减与格局阈值为显式启发式规则。紫微领域模型强调主题宫与关联宫。

采纳：统一输入；可靠排盘优先；本命与时间窗口组织；主题联宫；自然长文而非给用户倾倒 JSON。

不采纳：首版六体系扩张；把强弱数值当经验证概率；默认隐藏体系分歧；把固定阈值判格局当作唯一传统标准。whoami 的格局/调候/扶抑解释由宿主分开论证，必须引用计算事实，不能仅凭五行计数给唯一喜用。

验证边界：已做指定源码阅读，未运行 Yuan 全体系或验证其算法准确性。其六体系声明不等于 whoami 的功能范围。
