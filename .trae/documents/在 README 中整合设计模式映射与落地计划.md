## 目标
- 采用控制器+视图+模型（MVC）复合模式对现有代码进行解耦，不新增功能
- 明确模块职责、接口契约与数据流，记录可拓展方向，更新 README 的架构说明

## 当前映射
- 模型（Model）
  - `core/state.py` `GameState`、`Base`/`Unit`、`serialize/deserialize`
  - `core/map.py` `Map`、`generate`、`PLAIN/MOUNTAIN/RIVER`
  - 说明：仅维护游戏数据与业务规则，不依赖 UI 或输入
- 视图（View）
  - `renderer/pygame_renderer.py` 图形渲染（六边形地图/单位/基地/HUD）
  - `web/app.js` Canvas 渲染（六边形）
  - 说明：只读模型数据，提供 `render(state,tick)`；不执行业务变更
- 控制器（Controller）
  - 现状：`rts_pygame.py` 混合了输入处理、状态管理、渲染调度
  - 目标：抽出 `GameController` 负责输入→命令解析→调用模型/循环→调度视图

## 数据流（复合模式步骤）
- 用户与视图交互 → 控制器解释输入（快捷键/按钮） → 生成命令对象 `Action` → 调用 `SimulationLoop.step()/apply_action()` 更新模型 → 模型变更事件（可选：观察者） → 视图拉取模型并渲染 → 视图更新

## 模块与接口
- 控制器 `controllers/game_controller.py`
  - 责任：
    - 管理 UI 状态：`MENU/RUNNING/MAP_SELECT/GAMEOVER`
    - 统一键鼠输入：`handle_event(event)`（大小写兼容）
    - 调度循环：`tick_step()`（连续/逐步/暂停/倍速）
    - 地图选择与加载：`load_map(path)`、编辑器入口回调
  - 对外：
    - `start_random()`、`start_with_state(state)`
    - `restart()` 使用当前初始状态（随机/选择）
- 视图 `views/`
  - `views/pygame_view.py`：包装 `PygameRenderer` 与按钮绘制，暴露 `draw_menu/select/gameover/hud`
  - `views/web_view`：保留现有前端，文档记录接口契约
- 模型 `models/`
  - 引用现有 `core/*` 与 `ai/*`、`simulation/loop.py`
- 命令（Command）
  - 已有 `ai/policy.py` `Action`（移动/攻击/游走），控制器将 UI 输入转换为“控制命令”（暂停/倍速/逐步）并作用于 `SimulationLoop`
- 状态（State）
  - 控制器内封装 `UIState`，取代散落的条件分支；提供 `transition(to)`
- 观察者（Observer，记录可拓展方向）
  - 事件总线 `events/EventBus`（后续可选）：发布“基地被发现/HP 变化/单位死亡”，视图订阅以驱动弹幕/HUD

## 文件框架（仅文档与目录，不改功能）
- `controllers/game_controller.py`（新）
- `views/pygame_view.py`（新，封装现有渲染与菜单/选择界面绘制）
- `models/`（指向 `core/`/`ai/`/`simulation/`）
- `events/`（占位与 README 说明，可后续实现）
- `rts_pygame.py`：精简为入口，仅创建控制器与视图并运行

## README 更新内容
- 新增“设计模式与架构（MVC 复合模式）”小节：
  - 模型/视图/控制器职责与当前代码映射
  - 数据流 5 步说明与关键接口列表
  - 已使用模式：策略/命令/工厂/模板方法；可拓展模式：观察者/状态/适配器/装饰者
  - 不为用而用：记录扩展点与引入条件（复杂度 vs 收益）

## 重构步骤（不引入新功能）
1) 提取控制器文件，迁移 `rts_pygame.py` 的输入与状态逻辑到 `GameController`
2) 提取视图文件，迁移菜单/选择/结算的绘制辅助到 `pygame_view`
3) `rts_pygame.py` 仅负责初始化与主循环委托（控制器→视图）
4) 验证行为与原一致：菜单/选择/编辑器/逐步/暂停/倍速/重开/视角
5) 更新 README 的架构章节与接口追踪

## 验证与风险
- 验证：跑通所有现有交互流；确保控制器替换不影响模型与渲染
- 风险：文件移动可能引入导入路径问题；通过明确模块引用与 README 指引规避

确认后我将：
- 创建 `controllers/game_controller.py` 与 `views/pygame_view.py`，迁移逻辑与绘制辅助
- 精简 `rts_pygame.py` 为入口
- 更新 `README.md` 增加 MVC 章节与设计模式映射说明