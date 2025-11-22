## 架构对齐与现状
- 已有核心层：`core/map.py`、`core/entities.py`、`core/state.py`，含 `Map/Base/Unit/GameState` 与 `serialize()`。
- 已有逻辑与循环：`simulation/loop.py`（生产、移动/攻击、胜负判定）、`ai/policy.py`（简单策略）。
- 已有渲染接口：`renderer/base.py`（`Renderer` 抽象），现用 `renderer/char.py` 终端字符渲染；Web 端通过 `web/app.js` 用 Canvas 绘制并由 `web/server.py` 提供 `/api/state`。
- 目标：实现 Python 端的 `PygameRenderer`，满足图形化实时渲染与 HUD 要求，并与现有 `SimulationLoop` 无缝对接。

## 图形渲染实现（PygameRenderer）
- 新增类：`renderer/pygame_renderer.py`，实现接口：
  - `initialize()`：初始化 `pygame`、窗口、时钟、字体，读取配置（网格尺寸、颜色映射）。
  - `load_assets()`：准备地形/基地/单位的颜色与尺寸，预载字体与可选贴图（后续可替换）。
  - `render(game_state)`：调用分解方法：`render_map()`、`render_bases()`、`render_units()`、`render_hud()`，再 `present_frame()`。
  - `render_map()`：按 `GameState.map.grid` 绘制格子矩形（空地/山脉/河流颜色区分）。
  - `render_units()`：按阵营颜色绘制圆点/小矩形，依据 `Unit.kind` 可区分形状或大小。
  - `render_bases()`：以更大图标绘制，含血量条。
  - `render_hud()`：左上角显示 `tick`、双方单位数量、基地 HP；右上角显示 FPS。
  - `present_frame()`：`pygame.display.flip()` + `clock.tick(target_fps)` 控帧率。
- 坐标换算：`world_to_screen(x,y) -> (px,py)` 基于单元格边长 `cell_size`；留边距与安全裁剪。
- 交互输入：`process_input()`：窗口事件（退出）、可选暂停/速度滑条预留（快捷键占位）。

## 主循环整合
- 入口示例：`rts_sim.py` 或新建 `main_pygame.py`（保留现有入口不破坏 Web）。
  - `renderer = PygameRenderer()` → `renderer.initialize()` → 绑定 `SimulationLoop`。
  - 循环：
    1. `process_input()`（后续可扩展）
    2. `game_state.update()`（或调用 `SimulationLoop.step()`，固定 `tick_time`）
    3. `renderer.render(game_state)`
  - 结束：`renderer.close()`。
- 固定步长：将逻辑更新保持固定步，渲染可变量步（或统一固定帧率）。

## AI 决策与单位行为
- 接口预留：`ai/interfaces.py` 新增 `class IDecisionModel: decide(unit, game_state) -> Action`。
- 默认实现：`RandomDecisionModel`（若视野内无敌则随机游走，若有敌在射程内则攻击，否则接近）。
- 行为细化：
  - `find_targets()`：基于视野半径与阵营过滤。
  - `select_target()`：就近/最低 HP 策略。
  - `move_towards()`：简单网格邻居接近（后续可替换 A*）。
  - `random_move()`：在可通行邻居中采样移动。
  - `attack()`：基于 `attack_range` 与 `damage = attack - armor` 下限保护。

## 状态管理与基地生产
- `GameState`：
  - `add_unit()`、`remove_dead_units()`、`check_victory()` 完整工作流；补齐 `deserialize(dict) -> GameState`。
  - `tick` 自增与占用格更新 `update_occupied()`。
- `Base`：
  - 定时器 `production_timer` 与 `production_interval`，`update()` 到点 `produce_unit()` 随机生成三类单位（近战/远程/重甲）。

## 并发与网络接口（预留）
- 并发：`concurrency/interfaces.py`
  - `class IWorker: start/stop/submit_task`
  - `class ITaskScheduler: submit(task)` 与主循环对接处预留钩子。
- 网络：`network/interfaces.py`
  - `class INetworkSession: send_state/receive_input/sync`；现阶段沿用 `web/server.py` 的 HTTP/JSON。
- 序列化：`GameState.serialize()/deserialize()` 满足网络层同步要求。

## 文件与改动点
- 新增：`renderer/pygame_renderer.py`、`ai/interfaces.py`、`concurrency/interfaces.py`、`network/interfaces.py`。
- 更新：`core/state.py`（补充 `deserialize`）、入口脚本（新增或更新以选择渲染器）。
- 保持：现有 Web 端不受影响，可作为并行展示方式。

## 验证与测试
- 运行 Pygame 版，观察：网格绘制正确、单位移动与攻击、基地生产节奏、HUD 数值准确、帧率稳定。
- 压测：调大地图与单位数量，确认渲染与逻辑的性能边界。
- 回归：终端字符渲染与 Web Canvas 渲染仍可使用，数据一致性校验（`serialize()` 对齐）。

## 交付与后续扩展
- 交付：完整 `PygameRenderer`、接口占位与主循环整合。
- 后续：替换随机决策为 FSM/A*；引入线程池驱动 AI；网络对战使用 WebSocket/UDP；资源替换与动效。