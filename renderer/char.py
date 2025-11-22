from renderer.base import Renderer
from core.map import PLAIN, MOUNTAIN, RIVER

def symbol_for(unit):
    if unit.team == 'A':
        return {'Infantry':'a','Archer':'r','Cavalry':'c'}[unit.kind]
    return {'Infantry':'x','Archer':'y','Cavalry':'z'}[unit.kind]

class CharRenderer(Renderer):
    def render(self, gamestate, tick):
        canvas = [row[:] for row in gamestate.map.grid]
        canvas[gamestate.base_a.y][gamestate.base_a.x] = 'A'
        canvas[gamestate.base_b.y][gamestate.base_b.x] = 'B'
        cell_units = {}
        for u in gamestate.units:
            p = u.pos()
            cell_units.setdefault(p, []).append(u)
        for (x, y), lst in cell_units.items():
            canvas[y][x] = symbol_for(lst[-1])
        lines = []
        lines.append(f"回合: {tick}")
        lines.append(f"甲方基地HP: {max(0, gamestate.base_a.hp)}  乙方基地HP: {max(0, gamestate.base_b.hp)}  单位数: A {sum(1 for u in gamestate.units if u.team=='A')} / B {sum(1 for u in gamestate.units if u.team=='B')}")
        for y in range(gamestate.map.height):
            lines.append(''.join(canvas[y]))
        return '\n'.join(lines)