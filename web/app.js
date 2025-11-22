const UI = {
  button(text, cls, onClick) {
    const b = document.createElement('button');
    b.className = `btn ${cls||''}`;
    b.textContent = text;
    b.onclick = onClick;
    return b;
  },
  menu(items) {
    const m = document.getElementById('menu');
    items.forEach(i=>m.appendChild(UI.button(i.text, i.cls, i.onClick)));
  }
};

const API = {
  async state() {
    const r = await fetch('/api/state');
    return await r.json();
  },
  async control(cmd, value) {
    await fetch('/api/control', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({cmd, value}) });
  }
};

const View = {
  init() {
    this.canvas = document.getElementById('canvas');
    this.ctx = this.canvas.getContext('2d');
    const resize = ()=>{
      const rect = this.canvas.getBoundingClientRect();
      this.canvas.width = rect.width;
      this.canvas.height = rect.height;
    };
    window.addEventListener('resize', resize);
    resize();
  },
  draw(state) {
    const ctx = this.ctx;
    ctx.clearRect(0,0,this.canvas.width,this.canvas.height);
    const w = state.map.width; const h = state.map.height;
    const padLeft = 24, padRight = 24, padTop = 48, padBottom = 24;
    const usableW = Math.max(1, this.canvas.width - padLeft - padRight);
    const usableH = Math.max(1, this.canvas.height - padTop - padBottom);
    const size = Math.min(usableW / (Math.sqrt(3) * (w + 0.5)), usableH / (1.5 * h));
    const uiTop = padTop;
    function hexCenter(x,y){
      const cx = padLeft + size * Math.sqrt(3) * (x + 0.5 * (y & 1));
      const cy = uiTop + size * 1.5 * y;
      return [cx, cy];
    }
    function hexPath(cx, cy){
      ctx.beginPath();
      for (let i=0;i<6;i++){
        const ang = (60*i + 30) * Math.PI / 180;
        const px = cx + size * Math.cos(ang);
        const py = cy + size * Math.sin(ang);
        if (i===0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.closePath();
    }
    for (let y=0;y<h;y++){
      for (let x=0;x<w;x++){
        const c = state.map.grid[y][x];
        let color = '#0f1720';
        if (c === '.') color = '#182230';
        else if (c === '#') color = '#3b4252';
        else if (c === '~') color = '#1f6fd1';
        const [cx, cy] = hexCenter(x,y);
        ctx.fillStyle = color;
        hexPath(cx, cy);
        ctx.fill();
        ctx.save();
        ctx.strokeStyle = '#444a55';
        ctx.lineWidth = 0.75;
        ctx.setLineDash([2,2]);
        ctx.stroke();
        ctx.restore();
      }
    }
    const [ax, ay] = hexCenter(state.bases[0].x, state.bases[0].y);
    ctx.fillStyle = '#ffcc00';
    ctx.beginPath(); ctx.arc(ax, ay, size*0.6, 0, Math.PI*2); ctx.fill();
    const [bx, by] = hexCenter(state.bases[1].x, state.bases[1].y);
    ctx.fillStyle = '#ff3366';
    ctx.beginPath(); ctx.arc(bx, by, size*0.6, 0, Math.PI*2); ctx.fill();
    for (const u of state.units){
      const team = u.team === 'A' ? '#5bd87a' : '#f08bdc';
      const [ux, uy] = hexCenter(u.x, u.y);
      ctx.fillStyle = team;
      ctx.beginPath();
      ctx.arc(ux, uy, Math.max(3, size*0.35), 0, Math.PI*2);
      ctx.fill();
    }
  }
};

async function main(){
  UI.menu([
    { text:'暂停', cls:'', onClick:()=>API.control('pause') },
    { text:'继续', cls:'primary', onClick:()=>API.control('resume') }
  ]);
  const btnPause = document.getElementById('btnPause');
  const btnResume = document.getElementById('btnResume');
  const speed = document.getElementById('speed');
  const stats = document.getElementById('stats');
  btnPause.onclick = ()=>API.control('pause');
  btnResume.onclick = ()=>API.control('resume');
  speed.oninput = ()=>API.control('speed', parseFloat(speed.value));
  View.init();
  let last = 0; let frames = 0; let fps = 0;
  async function loop(ts){
    frames++;
    if (ts - last >= 1000){ fps = frames; frames = 0; last = ts; }
    const state = await API.state();
    View.draw(state);
    stats.textContent = `回合 ${state.tick} | 甲方HP ${state.bases[0].hp} | 乙方HP ${state.bases[1].hp} | FPS ${fps}`;
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
}

main();