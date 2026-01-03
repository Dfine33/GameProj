# RTS 对战模拟系统（图形化优先版）

## 项目结构

- `core/`
  - `map.py`：地图与地形
    - 常量：`PLAIN`/`MOUNTAIN`/`RIVER` `core/map.py:3-5`
    - `class Map(width,height,grid)` `core/map.py:7-12`
    - 生成函数：`generate(width,height)` 随机山脉与河流 `core/map.py:19-39`
  - `entities.py`：实体定义
    - `class Base(team,x,y,hp,spawn_cooldown)` `core/entities.py:1-8`
    - `class Unit(team,kind,x,y,atk,rng,spd,hp,armor,vision)` `core/entities.py:12-26`
  - `state.py`：游戏全局状态
    - `class GameState` 初始化、基地安置、单位列表、占用格、tick `core/state.py:7-17`
    - 占用更新/增删单位：`update_occupied`/`add_unit`/`remove_unit` `core/state.py:18-27`
    - 序列化/反序列化：`serialize()`/`deserialize()` `core/state.py:29-48,50-80`
    - 敌方基地与探索接口：`record_enemy_base`/`record_explored` `core/state.py:82-88`
    - 探索查询：`is_explored`/`get_explored_ratio`/`get_explored_cells` `core/state.py:90-99`
    - 基地放置/产兵与伤害：`place_bases`/`spawn_unit`/`damage_value` `core/state.py:114-128`

- `simulation/`
  - `loop.py`：主逻辑循环与行动应用
    - `class SimulationLoop(policy,renderer)` `simulation/loop.py:8-14`
    - 六边形移动：`step_towards(unit,dest)` 选取 6 邻居使 `hex_distance` 最小 `simulation/loop.py:15-30`
    - 随机游走：`wander(unit)` 从 6 邻居随机可行格 `simulation/loop.py:32-40`
    - 产兵：`spawn_from_base(base)` 基地周围邻接随机生成 `simulation/loop.py:42-57`
    - 行动应用：`apply_action(unit,action)` 移动/攻击/游走 `simulation/loop.py:59-78`
    - 步进：`step(print_every)` 与结束判定 `simulation/loop.py:80-95`
    - 执行：`run(max_ticks,print_every)` `simulation/loop.py:97-124`

- `ai/`
  - `policy.py`：策略与行动
    - `class Action(kind,target)` `ai/policy.py:3-6`
    - 抽象策略：`DecisionPolicy.decide` `ai/policy.py:8-10`
    - 简单策略：`SimplePolicy.decide` 基于视野与射程的最近目标 `ai/policy.py:12-32`
    - 两阶段策略：`TwoPhasePolicy` 侦察→总攻、敌方基地记忆 `ai/policy.py:34-72`
  - `interfaces.py`：接口占位（可扩展 FSM/A* 等）

- `renderer/`
  - `base.py`：渲染接口 `Renderer.render(gamestate,tick)` `renderer/base.py:1-3`
  - `char.py`：字符栅格渲染（终端） `renderer/char.py:9-25`
  - `pygame_renderer.py`：图形渲染（Pygame，六边形栅格）
    - 初始化：`initialize(gamestate)` 计算窗口尺寸与字体 `renderer/pygame_renderer.py:36-55`
    - 帧渲染：`render(gamestate,tick)` 计算可见集与调用各层渲染 `renderer/pygame_renderer.py:74-88`
    - 地图：`render_map(gamestate,vis)` 六边形绘制、未探索/已探索不可见遮罩、虚线描边 `renderer/pygame_renderer.py:90-120`
    - 基地：`render_bases(gamestate,vis)` 可见/永久标注与血条 `renderer/pygame_renderer.py:121-146`
    - 单位：`render_units(gamestate,vis)` 居中绘制 `renderer/pygame_renderer.py:148-161`
    - HUD：`render_hud(gamestate,tick)` 顶部信息、暂停/倍速/逐步控件 `renderer/pygame_renderer.py:163-240`
    - 视野：`compute_visibility(gamestate,side)` 六边形 LOS（山阻挡，河不阻挡） `renderer/pygame_renderer.py:242-271`
    - 叠加与描边：`_poly_overlay`/`_stroke_dashed` `renderer/pygame_renderer.py:273-304`

- `web/`
  - `server.py`：HTTP 服务，提供 `/api/state`、`/api/control`（暂停/继续/速度） `web/server.py:41-50,53-76`
  - `app.js`：Canvas 六边形渲染，单位/基地居中绘制与简单 UI `web/app.js:25-36,37-94`
  - `index.html` / `styles.css`：前端页面与样式

- `utils/`
  - `common.py`：工具函数
    - 网格邻居：`adjacent_positions`（方格） `utils/common.py:6-7`
    - 六边形邻居：`hex_neighbors`（odd-r） `utils/common.py:9-13`
    - 坐标转换：`oddr_to_cube`/`cube_to_oddr` `utils/common.py:15-28`
    - 六边形距离：`hex_distance` `utils/common.py:30-33`
    - 线段与取整：`cube_round`/`hex_line` `utils/common.py:35-64`

## 运行方式

- 图形版（Pygame）：
  - Windows PowerShell 执行：`python rts_pygame.py`
  - 控制：
    - 视角切换：`1` A 方、`2` B 方、`3` 上帝视角
    - 暂停/继续：`Space` 或右上角 `▶/⏸`
    - 倍速：`←/→` 或右上角 `- / +`
    - 逐步模式：`T` 切换；单步：`N` 或右上角 `⏭`
    - 返回主菜单：`Esc`

- Web 版（Canvas）：
  - 后端服务：`python web/server.py`
  - 浏览器访问：`http://localhost:8000/`
  - 顶部按钮可暂停/继续，滑条控制速度（接口见 `web/server.py:53-76`）

## 关键接口速览

- 地图与地形
  - `Map.in_bounds(x,y) -> bool` `core/map.py:13-14`
  - `Map.can_walk(x,y) -> bool` 仅平地可通行 `core/map.py:16-17`

- 实体与状态
  - `Base.pos() -> (x,y)` `core/entities.py:9-10`
  - `Unit.pos() -> (x,y)` `core/entities.py:25-26`
  - `GameState.serialize()/deserialize(dict)` `core/state.py:29-48,50-80`
  - `GameState.record_enemy_base(side,pos)` `core/state.py:82-83`
  - 探索接口：`record_explored` / `is_explored` / `get_explored_ratio` / `get_explored_cells` `core/state.py:85-99`
  - 产兵与伤害：`spawn_unit` / `damage_value` `core/state.py:119-128`

- 工具与计算
  - `hex_neighbors(x,y)` 六邻居 `utils/common.py:9-13`
  - `hex_distance(a,b)` 六边形距离 `utils/common.py:30-33`
  - `hex_line(a,b)` 六边形线段（LOS） `utils/common.py:50-64`

- 策略与循环
  - `DecisionPolicy.decide(unit,gamestate) -> Action` `ai/policy.py:8-10`
  - `SimplePolicy`/`TwoPhasePolicy` 视野判断与目标选择 `ai/policy.py:12-32,34-72`
  - `SimulationLoop.step()` 单次 tick 计算与渲染调用 `simulation/loop.py:80-95`

- 渲染层（Pygame）
  - `PygameRenderer.render_map` 未探索/已探索不可见/可见三层显示 `renderer/pygame_renderer.py:90-120`
  - `PygameRenderer.compute_visibility` 六边形 LOS（山阻挡，河不阻挡） `renderer/pygame_renderer.py:242-271`
  - 右上角控制：暂停/倍速/逐步/单步控件 `renderer/pygame_renderer.py:193-240`

## 设计要点

- 六边形栅格（odd-r，pointy-top）
  - 像素中心：`cx = size*sqrt(3)*(x + 0.5*(y&1))`，`cy = size*1.5*y + ui_top`
  - 视野半径使用六边形距离；遮挡用 `hex_line` 扫描，山阻挡/河不阻挡

- 探索与显示
  - 未探索：以普通地形底色绘制并浅灰遮罩，不泄露山/河
  - 已探索不可见：保留真实地形颜色并轻暗遮罩
  - 敌方基地：不可见但已知时以描边圆环永久标记

- 扩展接口
  - AI：新增策略实现只需继承 `DecisionPolicy` 并在入口选择策略
  - 并发/网络：`concurrency/interfaces.py` 与 `network/interfaces.py` 为占位接口
  - Web：`grid_type/layout` 供前端识别栅格布局，可扩展至视野遮挡

## 常见问题

- 运行崩溃（越界）：六边形 LOS 读取地形时已加入边界判断；如地图尺寸修改，请确保窗口尺寸与偏移计算一致（`renderer/pygame_renderer.py:36-40`）。
- 字体乱码：渲染器使用中文字体优先匹配并自动回退（`renderer/pygame_renderer.py:46-55`）。
- 调试：使用逐步模式（`T`/`N` 或右上角控件）逐 tick 检查单位决策与可见性变化。

## 开发建议

- 单元测试：可参考 pygame 社区的测试指南与贡献文档，逐步为六边形工具与策略增加测试用例。
- 性能：大地图下建议缓存六边形顶点坐标以减少每帧重复计算；或降低虚线描边开销。

## MVC 复合模式架构

- 模型（Model）
  - `core/state.py`、`core/map.py`、`core/entities.py` 仅维护数据与业务规则
  - 序列化/反序列化：`GameState.serialize/deserialize`
- 视图（View）
  - `renderer/pygame_renderer.py` 提供 `render(state,tick)`、HUD 与控件绘制
  - `views/pygame_view.py` 封装菜单/选择/结算绘制与弹幕更新
  - `web/app.js` Canvas 端渲染
- 控制器（Controller）
  - `controllers/game_controller.py` 统一输入事件、UI 状态机与循环调度
  - 对外方法：`start_random/start_with_state/restart/load_map`
- 数据流
  - 用户与视图交互 → 控制器解析 → 命令/循环更新模型 → 视图拉取模型渲染
- 已用模式
  - 策略：`DecisionPolicy/TwoPhasePolicy` 可替换决策
  - 命令：`Action` + `apply_action` 统一执行请求
  - 工厂：`spawn_unit`、`generate` 创建单位与地图
  - 模板方法：渲染流程骨架
- 可拓展模式（记录，不立即引入）
  - 观察者：事件总线 `EventBus`（HP/基地发现/单位死亡订阅）
  - 状态：`UIState` 与单位 FSM（替代分支）
  - 适配器/外观：噪声/寻路/网络抽象层
  - 装饰者：单位 Buff/Debuff 与地形加成

## 平衡配置与生成策略
- 常量集中：`core/balance.py`
  - `BASE_BUILD_POINTS=6` 每回合造兵点数（不累计）
  - `UNIT_COSTS` 与 `UNIT_STATS` 抽离，便于调参或自动优化
- 生成策略：`ai/spawn_strategy.py`
  - `ISpawnStrategy.choose_units(points, team, state)` 返回兵种列表
  - 默认 `RandomSpawnStrategy` 按点数随机填充
- 行为策略：`ai/unit_policies.py`
  - `Scout/Infantry/Archer` 分兵种策略，组合为 `CompositePolicy`
  - 入口选用：`rts_pygame.py:run_mvc()` 设置 `CompositePolicy` 为当前策略

## 模式总览（EVE 与 PVE）

- 菜单与入口
  - 一级菜单：`EVE 电脑对战 / PVE 人机对战 / PVP（占位） / 地图编辑器 / 调试工具 / 退出` `views/pygame_view.py:18-26`
  - EVE/PVE 二级菜单：`随机地图 / 选择地图 / 返回主菜单` `views/pygame_view.py:28-34`
  - 入口控制与状态机：`controllers/game_controller.py:61-121,146-184`

- EVE（电脑对战）
  - 双方均由 AI 控制：组合兵种策略 `CompositePolicy` `ai/unit_policies.py:1-70`
  - 运行模式：连续/逐步均支持；右上控件控制暂停、倍速、逐步/单步 `renderer/pygame_renderer.py:239-292`
  - 地图来源：随机或选择 `maps/*.json`；结束界面支持重开与回主菜单 `controllers/game_controller.py:311-320`

- PVE（人机对战）
  - 阵营选择：进入对局前选择红队/蓝队；视野锁定到所选阵营 `controllers/game_controller.py:185-204,355-361`
  - 严格逐帧回合制：操作阶段→结算阶段→下一回合 `simulation/loop.py:62-104`
    - 操作阶段：玩家进行招募与单位指令，AI 同时给出行动
    - 结算阶段顺序：生成→攻击→移动，回合数仅在结算后递增
  - 视野与到达约束：
    - 移动/预览仅允许到“可见或已探索”的可走格；基地视作障碍 `simulation/loop.py:26-39,100-106`
  - 玩家招募（基地面板）：
    - 面板内容：当回合点数、三兵种属性与消耗、撤回 `renderer/pygame_renderer.py:343-381`
    - 交互：点击基地开/关面板，选兵种后高亮 1 格可放置空地；点击加入队列并扣点数；撤回恢复点数 `controllers/game_controller.py:256-289,415-431`
  - 玩家单位操作（单位面板）：
    - 面板内容：血量条、移动/攻击模式切换、可攻击目标列表与撤回 `renderer/pygame_renderer.py:382-421`
    - 移动：显示本回合可达高亮；点击生成实际可走 BFS 路径预览并截断到 `spd` 步 `controllers/game_controller.py:430-476`
    - 攻击：目标高亮与箭头预览，设置指令 `renderer/pygame_renderer.py:324-342`
  - 预览与一致性：
    - 招募预览：半透明单位叠加在放置格 `renderer/pygame_renderer.py:309-315`
    - 移动预览：渲染 BFS 路径；结算按该路径推进，避免“预览与实际不同” `renderer/pygame_renderer.py:312-329, simulation/loop.py:94-129`
    - 结束按钮点击后自动清空面板与预览 `controllers/game_controller.py:246-254`
  - 冲突仲裁：
    - 同格竞争：按 `spd`→`hp`→`atk`→对象 id 排序选赢家；每步仅推进一格并释放原占用 `simulation/loop.py:110-129`
    - 攻击批量伤害：先汇总再统一应用，支持互相击杀 `simulation/loop.py:73-85`

- 辅助与调试
  - 视野与路径调试器：主菜单“调试工具”，支持放置地形/单位、LOS 与 BFS 路径检查 `tools/vision_path_tester.py:1-280`，入口 `controllers/game_controller.py:124-137`

## 电脑策略总览

- 策略层次
  - 单位行为策略：按兵种分派 `Scout/Infantry/Archer`，组合为 `CompositePolicy` `ai/unit_policies.py:58-69`
  - 全局两阶段策略：`TwoPhasePolicy`（侦察→总攻，记录敌方基地）`ai/policy.py:34-72`
  - 简单策略：`SimplePolicy`（最近目标优先，射程内攻击）`ai/policy.py:12-33`

- 决策输入
  - 视野：六边形 LOS，山阻挡、河不阻挡 `renderer/pygame_renderer.py:422-451`
  - 状态：单位/基地位置、射程 `rng`、移动点数 `spd`、六边形距离 `hex_distance`
  - 敌方基地记忆：一旦在视野内看到敌方基地，写入 `known_enemy_base[side]` `core/state.py:82-83`

- 行为规则
  - 侦察兵（ScoutPolicy）：优先探索远点；看到敌方基地后向基地推进并在射程内攻击 `ai/unit_policies.py:7-26`
  - 步兵（InfantryPolicy）：选择最近目标，近战推进；射程内攻击，否则靠近 `ai/unit_policies.py:28-41`
  - 弓箭手（ArcherPolicy）：选择最近目标，优先在射程边缘攻击并保持距离 `ai/unit_policies.py:43-56`
  - 两阶段策略（TwoPhasePolicy）：视野内记录基地；有已知基地则向基地推进；否则选择最近可见目标或远点探索 `ai/policy.py:38-72`
  - 默认行为（无目标）：`wander` 随机游走

- 生成策略
  - 点数制：每回合 `BASE_BUILD_POINTS=6`，不累计 `core/balance.py:1`
  - 随机策略：`RandomSpawnStrategy` 按点数随机填充兵种列表，溢出忽略 `ai/spawn_strategy.py:1-26`

- 结算流程（对 AI 同样适用）
  - 顺序：生成 → 攻击（批量伤害）→ 移动（两阶段仲裁）
  - 攻击：汇总伤害并统一应用，支持互相击杀 `simulation/loop.py:73-85`
  - 移动：每步一格，意图收集后按 `spd→hp→atk→id` 仲裁同格竞争；基于“已知可走”格，禁止进入基地格 `simulation/loop.py:108-129,26-39,100-106`

- 约束与边界
  - 移动/生成仅在可走且未占用格执行；玩家侧与电脑侧一致使用占用集合与基地障碍判定
  - 视野与探索：AI 决策依赖当前视野与已探索信息；不可见的未知区域不参与可达判断
 
## 文件索引（逐文件说明）
- 顶层
  - `rts_pygame.py`：应用入口，创建 `PygameRenderer`/`PygameView`/`GameController` 并运行
- core/
  - `core/map.py`：地形常量与地图类（宽高与网格），随机生成与可走判断
  - `core/entities.py`：`Base`（含每回合点数/增益）与 `Unit` 属性模型
  - `core/state.py`：全局状态、单位列表/占用集、序列化/反序列化、探索与基地记录
  - `core/balance.py`：造兵点数与兵种属性/成本配置
- simulation/
  - `simulation/loop.py`：回合引擎；阶段（操作/结算）、预览路径、攻击批量伤害、移动仲裁与同格竞争
- ai/
  - `ai/policy.py`：`Action` 类型；`DecisionPolicy` 抽象；`SimplePolicy` 与 `TwoPhasePolicy`
  - `ai/unit_policies.py`：分兵种策略（Scout/Infantry/Archer）与 `CompositePolicy`
  - `ai/spawn_strategy.py`：`ISpawnStrategy` 与 `RandomSpawnStrategy`
- renderer/
  - `renderer/base.py`：渲染接口定义
  - `renderer/pygame_renderer.py`：六边形绘制、HUD/控件、预览叠加、LOS 计算
  - `renderer/char.py`：终端字符渲染（用于非图形环境）
- controllers/
  - `controllers/game_controller.py`：菜单/模式/输入事件；PVE 面板交互（招募/移动/攻击/撤回）；预览数据注入
- views/
  - `views/pygame_view.py`：主菜单/二级菜单与结算界面按钮、悬浮/选中态视觉反馈
- utils/
  - `utils/common.py`：六边形工具集（邻居/距离/线段/坐标转换）
- tools/
  - `tools/vision_path_tester.py`：独立调试器，放置障碍/单位/目标，检查 LOS 与 BFS 路径并可保存场景
- web/
  - `web/server.py`：HTTP 服务（状态与控制接口）
  - `web/app.js`：Canvas 端六边形渲染与简单 UI
- 其他
  - `map_editor.py`：地图编辑器（地形/镜像放置、命名保存、基地摆放）

