import random
import sys
import threading
import time
from core.state import GameState
from utils.common import hex_neighbors, hex_distance, hex_line
from ai.spawn_strategy import RandomSpawnStrategy
from ai.policy import Action

class SimulationLoop:
    def __init__(self, policy, renderer=None, initial_state=None, spawn_strategy=None):
        self.policy = policy
        self.renderer = renderer
        self.state = initial_state if initial_state is not None else GameState()
        self.lock = threading.Lock()
        self.spawn_strategy = spawn_strategy or RandomSpawnStrategy()
        self.await_human = False
        self.human_ready = True
        self.player_team = None
        self.player_points = 0
        self.player_recruits = []
        self.player_actions = {}
        self._vis_cache = {'A': set(), 'B': set()}

    def start_player_phase(self):
        if not self.await_human or self.player_team not in ('A','B'):
            return
        base = self.state.base_a if self.player_team == 'A' else self.state.base_b
        self.player_points = getattr(base, 'build_points_per_turn', 0) + getattr(base, 'build_point_bonus', 0)
        self.player_recruits = []
        self.player_actions = {}
        self._recruit_locks = set()

    def can_recruit(self, kind):
        from core.balance import UNIT_COSTS
        return self.player_points >= UNIT_COSTS.get(kind, 999)

    def queue_recruit(self, base, kind, pos):
        from core.balance import UNIT_COSTS
        if not self.can_recruit(kind):
            return False
        if not self.state.map.in_bounds(pos[0], pos[1]):
            return False
        if not self.state.map.can_walk(pos[0], pos[1]):
            return False
        if (pos[0], pos[1]) in self.state.occupied:
            return False
        lock = getattr(self, '_recruit_locks', set())
        if (pos[0], pos[1]) in lock:
            return False
        self.player_recruits.append({'base': base, 'team': base.team, 'kind': kind, 'pos': pos})
        lock.add((pos[0], pos[1]))
        self._recruit_locks = lock
        self.player_points -= UNIT_COSTS[kind]
        return True

    def undo_last_recruit(self):
        from core.balance import UNIT_COSTS
        if self.player_recruits:
            last = self.player_recruits.pop()
            self.player_points += UNIT_COSTS.get(last['kind'], 0)
            lock = getattr(self, '_recruit_locks', set())
            lock.discard((last['pos'][0], last['pos'][1]))
            self._recruit_locks = lock
            return True
        return False

    def set_unit_action(self, unit, action):
        self.player_actions[unit] = action

    def step_towards(self, unit, dest):
        ux, uy = unit.pos()
        nbrs = hex_neighbors(ux, uy)
        random.shuffle(nbrs)
        best = None
        best_d = 10**9
        for nx, ny in nbrs:
            if self._is_known_walkable(unit.team, nx, ny) and (nx, ny) not in self.state.occupied:
                d = hex_distance((nx,ny), dest)
                if d < best_d:
                    best_d = d
                    best = (nx, ny)
        if best is not None:
            unit.x, unit.y = best
            return True
        return False

    def wander(self, unit):
        nbrs = hex_neighbors(unit.x, unit.y)
        random.shuffle(nbrs)
        for nx, ny in nbrs:
            if self._is_known_walkable(unit.team, nx, ny) and (nx, ny) not in self.state.occupied:
                unit.x = nx
                unit.y = ny
                return True
        return False

    def spawn_from_base(self, base):
        points = getattr(base, 'build_points_per_turn', 0) + getattr(base, 'build_point_bonus', 0)
        kinds = self.spawn_strategy.choose_units(points, base.team, self.state)
        if not kinds:
            return
        spots = [p for p in hex_neighbors(base.x, base.y) if self.state.map.in_bounds(p[0], p[1])]
        random.shuffle(spots)
        for kind in kinds:
            for sx, sy in spots:
                if self.state.map.can_walk(sx, sy) and (sx, sy) not in self.state.occupied:
                    nu = self.state.spawn_unit(base.team, (sx, sy), kind)
                    self.state.add_unit(nu)
                    break

    def collect_actions(self):
        acts = []
        for u in list(self.state.units):
            if self.await_human and self.player_team and u.team == self.player_team:
                act = self.player_actions.get(u, Action('idle', None))
            else:
                act = self.policy.decide(u, self.state)
            acts.append((u, act))
        return acts

    def resolve_attacks(self, actions):
        dmg_map = {}
        for u, act in actions:
            if act.kind == 'attack':
                tgt = act.target
                if hasattr(tgt, 'pos') and hasattr(tgt, 'hp'):
                    if hex_distance(u.pos(), tgt.pos()) <= u.rng:
                        dmg = self.state.damage_value(u, tgt)
                        dmg_map[tgt] = dmg_map.get(tgt, 0) + dmg
        for tgt, total in dmg_map.items():
            tgt.hp -= total
        # 统一清理死亡单位
        dead = [x for x in self.state.units if hasattr(x, 'hp') and x.hp <= 0]
        for d in dead:
            self.state.remove_unit(d)

    def resolve_movements(self, actions):
        movers = []
        move_paths = {}
        for u, act in actions:
            if act.kind == 'move_towards':
                movers.append((u, act.target))
            elif act.kind == 'move_path':
                movers.append((u, None))
                move_paths[u] = list(act.target) if isinstance(act.target, list) else []
            elif act.kind == 'wander':
                movers.append((u, None))
        if not movers:
            return
        max_spd = max(u.spd for u, _ in movers)
        occupied = set(self.state.occupied)
        # 基地加入占用，禁止踏入基地格
        occupied.add(self.state.base_a.pos())
        occupied.add(self.state.base_b.pos())
        for step in range(max_spd):
            intents = {}
            candidates = []
            for u, tgt in movers:
                if u.spd <= step:
                    continue
                if u in move_paths and move_paths[u]:
                    # 路径驱动：沿预览路径推进一格
                    path = move_paths[u]
                    try:
                        idx = path.index(u.pos())
                    except ValueError:
                        # 当前位置不在路径上，直接停止路径驱动
                        continue
                    if idx + 1 < len(path):
                        nx, ny = path[idx + 1]
                        if self._is_known_walkable(u.team, nx, ny) and (nx, ny) not in occupied:
                            best = (nx, ny)
                        else:
                            best = None
                    else:
                        best = None
                elif tgt is None:
                    nbrs = hex_neighbors(u.x, u.y)
                    best = None
                    for nx, ny in nbrs:
                        if self._is_known_walkable(u.team, nx, ny) and (nx, ny) not in occupied:
                            best = (nx, ny)
                            break
                else:
                    nbrs = hex_neighbors(u.x, u.y)
                    best = None
                    best_d = 10**9
                    for nx, ny in nbrs:
                        if self._is_known_walkable(u.team, nx, ny) and (nx, ny) not in occupied:
                            d = hex_distance((nx, ny), tgt)
                            if d < best_d:
                                best_d = d
                                best = (nx, ny)
                if best is not None:
                    intents.setdefault(best, []).append(u)
                    candidates.append((u, best))
            # 仲裁
            for dest, us in intents.items():
                if len(us) == 1:
                    winner = us[0]
                else:
                    us.sort(key=lambda x: (-x.spd, -x.hp, -x.atk, id(x)))
                    winner = us[0]
                wx, wy = dest
                prev = winner.pos()
                winner.x, winner.y = wx, wy
                occupied.add((wx, wy))
                # 释放原占用，允许同回合后续推进经过该格
                if prev in occupied:
                    occupied.discard(prev)
        self.state.update_occupied()

    def apply_action(self, unit, action):
        if action.kind == 'attack':
            target = action.target
            if hasattr(target, 'pos'):
                if hasattr(target, 'hp'):
                    if hex_distance(unit.pos(), target.pos()) <= unit.rng:
                        dmg = self.state.damage_value(unit, target)
                        target.hp -= dmg
                        if hasattr(target, 'kind') and target.hp <= 0:
                            self.state.remove_unit(target)
            else:
                return
        elif action.kind == 'move_towards':
            for _ in range(unit.spd):
                if self.step_towards(unit, action.target):
                    self.state.occupied.add(unit.pos())
        elif action.kind == 'wander':
            for _ in range(unit.spd):
                if self.wander(unit):
                    self.state.occupied.add(unit.pos())

    def step(self, print_every=10):
        with self.lock:
            self.state.update_occupied()
            # 预计算双方可见集
            self._vis_cache['A'] = self._compute_visibility('A')
            self._vis_cache['B'] = self._compute_visibility('B')
            actions = self.collect_actions()
            progressed = False
            if not (self.await_human and not self.human_ready):
                # 生成阶段：AI 阵营自动生成，玩家阵营根据队列生成
                if self.await_human and self.player_team in ('A','B'):
                    if self.player_team == 'A':
                        self.spawn_from_base(self.state.base_b)
                    else:
                        self.spawn_from_base(self.state.base_a)
                    for rec in self.player_recruits:
                        x, y = rec['pos']
                        if self._is_known_walkable(rec['team'], x, y) and (x, y) not in self.state.occupied:
                            nu = self.state.spawn_unit(rec['team'], (x, y), rec['kind'])
                            self.state.add_unit(nu)
                else:
                    self.spawn_from_base(self.state.base_a)
                    self.spawn_from_base(self.state.base_b)
                self.resolve_attacks(actions)
                self.resolve_movements(actions)
                self.human_ready = False if self.await_human else True
                progressed = True
            if self.renderer is not None and self.state.tick % print_every == 0:
                out = self.renderer.render(self.state, self.state.tick)
                if out:
                    print(out)
                    sys.stdout.flush()
            if progressed:
                self.state.tick += 1
                # 清空玩家队列，准备下一回合
                if self.await_human:
                    self.player_recruits = []
                    self.player_actions = {}
                    self.start_player_phase()
            cont = self.state.base_a.hp > 0 and self.state.base_b.hp > 0
            return cont

    def _compute_visibility(self, side):
        vis = set()
        units = [u for u in self.state.units if u.team == side]
        for u in units:
            rng = u.vision
            ux, uy = u.pos()
            for y in range(self.state.map.height):
                for x in range(self.state.map.width):
                    if hex_distance((ux, uy), (x, y)) <= rng:
                        line = hex_line((ux, uy), (x, y))
                        blocked = False
                        for lx, ly in line[1:]:
                            if not self.state.map.in_bounds(lx, ly):
                                blocked = True
                                break
                            tile = self.state.map.grid[ly][lx]
                            if tile == '#':  # MOUNTAIN 阻挡
                                blocked = True
                                break
                        if not blocked:
                            vis.add((x, y))
        return vis

    def _is_known_walkable(self, side, x, y):
        if not self.state.map.in_bounds(x, y):
            return False
        if not self.state.map.can_walk(x, y):
            return False
        # 基地视作障碍
        if (x, y) == self.state.base_a.pos() or (x, y) == self.state.base_b.pos():
            return False
        known = (x, y) in self._vis_cache.get(side, set()) or (x, y) in self.state.explored.get(side, set())
        return known

    def preview_path(self, unit, target):
        # BFS 限制在可行且“已知”的格上
        from collections import deque
        sx, sy = unit.pos()
        tx, ty = target
        if not self._is_known_walkable(unit.team, tx, ty):
            return []
        dq = deque()
        dq.append((sx, sy))
        prev = {}
        seen = {(sx, sy)}
        while dq:
            x, y = dq.popleft()
            if (x, y) == (tx, ty):
                break
            for nx, ny in hex_neighbors(x, y):
                if (nx, ny) in seen:
                    continue
                if self._is_known_walkable(unit.team, nx, ny) and (nx, ny) not in self.state.occupied:
                    seen.add((nx, ny))
                    prev[(nx, ny)] = (x, y)
                    dq.append((nx, ny))
        path = []
        cur = (tx, ty)
        if cur not in prev and cur != (sx, sy):
            return []
        while cur != (sx, sy):
            path.append(cur)
            cur = prev.get(cur, (sx, sy))
        path.append((sx, sy))
        path.reverse()
        return path

    def run(self, max_ticks=1000, print_every=10):
        random.seed()
        while self.state.tick < max_ticks:
            cont = self.step(print_every)
            if not cont:
                break
        if self.renderer is not None:
            out = self.renderer.render(self.state, self.state.tick)
            if out:
                print(out)
        if self.state.base_a.hp <= 0 and self.state.base_b.hp <= 0:
            print('平局')
            if self.renderer is not None:
                sys.stdout.flush()
        elif self.state.base_a.hp <= 0:
            print('胜利方：乙方')
            print('胜利方法：攻破对方基地')
            if self.renderer is not None:
                sys.stdout.flush()
        elif self.state.base_b.hp <= 0:
            print('胜利方：甲方')
            print('胜利方法：攻破对方基地')
            if self.renderer is not None:
                sys.stdout.flush()
        else:
            print('未分胜负')
            if self.renderer is not None:
                sys.stdout.flush()
