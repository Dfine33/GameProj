import math

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def adjacent_positions(x, y):
    return [(x+1,y),(x-1,y),(x,y+1),(x,y-1),(x+1,y+1),(x-1,y-1),(x+1,y-1),(x-1,y+1)]

def hex_neighbors(x, y):
    if y % 2 == 0:
        return [(x+1,y),(x-1,y),(x,y+1),(x,y-1),(x-1,y+1),(x-1,y-1)]
    else:
        return [(x+1,y),(x-1,y),(x,y+1),(x,y-1),(x+1,y+1),(x+1,y-1)]

def oddr_to_cube(x, y):
    q = x - ((y - (y & 1)) // 2)
    r = y
    cx = q
    cz = r
    cy = -cx - cz
    return (cx, cy, cz)

def cube_to_oddr(cx, cy, cz):
    q = cx
    r = cz
    x = q + ((r - (r & 1)) // 2)
    y = r
    return (x, y)

def hex_distance(a, b):
    ax, ay, az = oddr_to_cube(a[0], a[1])
    bx, by, bz = oddr_to_cube(b[0], b[1])
    return max(abs(ax-bx), abs(ay-by), abs(az-bz))

def cube_round(x, y, z):
    rx = round(x)
    ry = round(y)
    rz = round(z)
    dx = abs(rx - x)
    dy = abs(ry - y)
    dz = abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return (rx, ry, rz)

def hex_line(a, b):
    ax, ay, az = oddr_to_cube(a[0], a[1])
    bx, by, bz = oddr_to_cube(b[0], b[1])
    N = max(abs(ax-bx), abs(ay-by), abs(az-bz))
    res = []
    if N == 0:
        return [a]
    for i in range(N+1):
        t = i / float(N)
        lx = ax + (bx - ax) * t
        ly = ay + (by - ay) * t
        lz = az + (bz - az) * t
        rx, ry, rz = cube_round(lx, ly, lz)
        res.append(cube_to_oddr(rx, ry, rz))
    return res

def get_local_ip():
    """
    Get the local LAN IP address of the machine.
    Returns '127.0.0.1' if no network interface is found or on error.
    """
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP