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

