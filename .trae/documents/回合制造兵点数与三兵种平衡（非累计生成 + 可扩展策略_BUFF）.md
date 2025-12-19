## 需求对齐
- 初始造兵点数：6（每回合，不累计）
- 视野：侦察兵=5、步兵=3、弓箭手=4
- 抽离平衡配置：新增 `core/balance.py` 管理兵种数值与点数、基地每回合点数
- 分兵种行为策略：将不同兵种的 AI 行为分开实现，统一通过组合策略使用

## 设计与文件
- 新增：`core/balance.py`
  - `BASE_BUILD_POINTS = 6`
  - `UNIT_COSTS = {'Scout':2,'Infantry':3,'Archer':3}`（可调）
  - `UNIT_STATS = { kind: {hp, atk, armor, rng, spd, vision} }`
    - Scout: vision=5、spd=3、hp=35、atk=7、armor=2、rng=2
    - Infantry: vision=3、spd=1、hp=80、atk=15、armor=5、rng=1
    - Archer: vision=4、spd=2、hp=55、atk=11、armor=1、rng=3
- 生成策略接口：`ai/spawn_strategy.py`
  - `ISpawnStrategy.choose_units(points, team, state)`→返回兵种列表
  - 默认 `RandomSpawnStrategy`：随机填充到点数耗尽
- 分兵种行为策略：`ai/unit_policies.py`
  - 抽象 `UnitPolicy`（继承 `DecisionPolicy`）
  - `ScoutPolicy`：偏探索，优先远点/视野覆盖
  - `InfantryPolicy`：偏近战，优先最近目标推进
  - `ArcherPolicy`：保持距离，优先在射程边缘攻击
  - 组合策略 `CompositePolicy`：按 `unit.kind` 分派到对应策略
- 模型改动：
  - `core/entities.Base` 增加 `build_points_per_turn=BASE_BUILD_POINTS`、`build_point_bonus=0`
  - `core/state.spawn_unit(team,pos,kind)` 按 `UNIT_STATS` 生成
  - `serialize/deserialize` 包含新增字段
- 循环改动：`simulation/loop.py`
  - `SimulationLoop(spawn_strategy=RandomSpawnStrategy(), decision_policy=CompositePolicy(...))`
  - `spawn_from_base(base)`：每回合 `points=base.build_points_per_turn+base.build_point_bonus`，用完即止；在 `hex_neighbors` 上逐个放置

## 验证
- 连续/逐步模式，回合点数始终为 6；生成遵循点数与可放置格
- 三兵种视野分别为 5/3/4，行为符合各自策略特征
- 配置集中于 `core/balance.py`，后续仅改此文件即可调整数值

## 不增功能的扩展记录
- 地图资源 BUFF：在 `build_point_bonus` 写入当回合增益
- 玩家 UI：将 `ISpawnStrategy` 替换为“玩家队列策略”
- 自动调参：AI 或脚本读取/写入 `core/balance.py` 进行平衡性搜索

确认后我将按以上方案实现，并在 README 的“设计要点/平衡配置”处注明常量文件与策略分派接口。