import os
import sys

# 自动将 src 加入 Python 路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

if __name__ == "__main__":
    try:
        from src.main import run_mvc
        run_mvc()
    except ImportError:
        # Fallback if run_mvc isn't importable directly or src module not found
        import runpy
        runpy.run_module('src.main', run_name='__main__', alter_sys=True)
