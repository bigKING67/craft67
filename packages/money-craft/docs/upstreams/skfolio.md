# skfolio：组合历史数据入口的有界评估

核对日期：2026-09-20。固定官方提交 `c99fcf71349e2df4a7a1033ee85ca2e9ced9abee`；不是对 skfolio 全部功能的审查。Money Craft 当前稳定组合核心做持仓快照、费用和假设压力审计，没有历史收益矩阵、协方差或优化器。

本轮决定：**DEFER 运行时接入；保留候选地位，记录未来数据准入要求。** 没有新增依赖、复制算法进入运行核心或改变已安装 Skill。来源级 reviewed_revision、absorbed_revision 仍为 null。

## 来源与实际阅读范围

[固定提交](https://github.com/skfolio/skfolio/tree/c99fcf71349e2df4a7a1033ee85ca2e9ced9abee)由公开分支查询取得。7个捕获文件均核对 SHA-256 与固定 Git tree 的 blob SHA-1，tree 未截断。5个文件完整阅读，README和项目配置仅阅读下列范围。

| 路径 | 已读范围 | SHA-256 |
|---|---|---|
| `LICENSE` | FULL | `07b8dfceb7b319e5145e7b1594d2cdaf94d924d78166d28951d4b360a4dc5844` |
| `README.rst` | PARTIAL: introduction, installation and Key Concepts (lines54-144) | `fe951f16c4d00a6a623bb86a326292993e19c7e326d8a67ea826569f96ccee6e` |
| `pyproject.toml` | PARTIAL: project metadata and dependency groups (lines1-135) | `b913fb2b6780603c3f02bf7bd05b96b6a239f2b6045cecf6c36897630e1fef84` |
| `src/skfolio/preprocessing/_returns.py` | FULL | `072c1ac92b4c5155c0f133874132f1e43c3e9e770f155d1a11f085a48fa346da` |
| `src/skfolio/base.py` | FULL | `1bc172d9d71b4638e89b82ae99a5776119f58b34d5fcd07ca94dbe455e28f0ff` |
| `src/skfolio/pre_selection/_select_complete.py` | FULL | `efb404a71d597e22e948aaf40a54bf725ccaa6e87c80724fc220e4c2e2f4c4fb` |
| `tests/test_preprocessing/test_returns.py` | FULL | `3751413305717ac13886af3687faa76ff1cc1031e335799b99848f43f6752bd6` |

[固定许可证](https://github.com/skfolio/skfolio/blob/c99fcf71349e2df4a7a1033ee85ca2e9ced9abee/LICENSE)为 BSD-3-Clause，SHA-256 `07b8dfceb7b319e5145e7b1594d2cdaf94d924d78166d28951d4b360a4dc5844`。所读Python文件声明同一SPDX许可；base.py另注明源自scikit-learn及其归属。本次固定tree中未发现另一个标准命名的LICENSE/NOTICE/COPYING/ATTRIBUTION声明；这不是对未读内容的完整许可意见。上游原文只保存在忽略目录用于核验，公开材料仅记录原创结论及元数据。

登记路径修复：固定tree与pyproject均证明入口是 `README.rst`，原登记的 `README.md` 不存在。本轮更正并跟踪 `pyproject.toml` 和 `tests/test_preprocessing/test_returns.py`，以便观察依赖和收益转换合同。原始登记决策保留为历史记录。

## 读取与运行得到的结论

1. `prices_to_returns` 支持简单/对数收益，默认前向填充。合成价格序列 `100 → 缺失 → 110 → 121` 在默认设置下产生 `0 → 10% → 10%`；这包含插补形成的零收益。它是明确的上游默认行为，本轮没有将其判断为上游缺陷。
2. `fill_nan=False, drop_inceptions_nan=False` 可保留缺失传播。只设置 `fill_nan=False` 时，默认删行会跨过缺失日期，产生跨日变动；不能在未检查间隔时当作等间隔收益直接年化。
3. `SelectComplete` 默认只按首尾缺失排除资产；内部缺失需显式选择相应选项。此项为完整源码阅读结论，未执行该类或完整skfolio包。
4. 上游README强调参数敏感、换手、样本外评估与防泄漏；这与Money Craft要求先验证数据和假设相容，但不能据此证明某优化方法适合用户。
5. base.py所示有状态/无状态变换与组合估计器接口有其机器学习语境；目前快照审计没有对应调用方，不迁入这套架构。

离线实测只导入已核验的 `_returns.py`，复用现有隔离数据运行时的numpy/pandas；4项行为检查通过。未安装skfolio、未跑求解器或风险模型，未声称完成上游测试套件。脚本和结果见私有验收回执索引。

## 重新评估的具体条件

有真实、已授权的历史风险或配置比较任务，且能提供以下输入时再启动适配器候选：

- 同一时间口径的证券身份、币种、复权/分红处理与价格/净值序列，记录来源和采集时间；交易币种不替代经济敞口。
- 单调、唯一的日期索引及明确交易日历，解释缺失、停牌、成立/退市与不可交易时段；插补/删行记录可重放，保留原始序列。
- 明确收益定义、采样间隔与年化规则；保留缺口或跨日区间，不能静默制造零收益。
- 训练、选股、估计与评估时间边界；预处理只使用允许的信息集，防止未来可知性和幸存者偏差。
- 与等权/现有配置比较的样本外方案，加入换手、费用及可投资约束；没有回测证据时不输出“最优”。

这些是后续立项的输入条件，不表示已经实现时间序列准入器。当前20项股票持仓加假设冲击不能替代历史收益矩阵；所以本轮不改变冻结组合核心，也不推进 absorbed_revision。

## 尚未覆盖

本次刷新发现旧观察提交到当前提交在原登记范围内有45个路径变化，未逐项审读这些差异。完整优化、walk-forward、求解器、概率/预测表现、所有上游模块和依赖安全均未验收。策引的新完整目录/正文快照也不属于本次skfolio评估，不据此刷新策引审读版本。
