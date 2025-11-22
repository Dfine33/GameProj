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
    const w = state.map.width;
    const h = state.map.height;
    const cw = Math.floor(this.canvas.width / w);
    const ch = Math.floor(this.canvas.height / h);
    for (let y=0;y<h;y++){
      for (let x=0;x<w;x++){
        const c = state.map.grid[y][x];
        let color = '#0f1720';
        if (c === '.') color = '#182230';
        else if (c === '#') color = '#3b4252';
        else if (c === '~') color = '#1f6fd1';
        ctx.fillStyle = color;
        ctx.fillRect(x*cw, y*ch, cw-1, ch-1);
      }
    }
    ctx.fillStyle = '#ffcc00';
    ctx.fillRect(state.bases[0].x*cw, state.bases[0].y*ch, cw-1, ch-1);
    ctx.fillStyle = '#ff3366';
    ctx.fillRect(state.bases[1].x*cw, state.bases[1].y*ch, cw-1, ch-1);
    for (const u of state.units){
      const team = u.team === 'A' ? '#5bd87a' : '#f08bdc';
      ctx.fillStyle = team;
      ctx.beginPath();
      ctx.arc(u.x*cw + cw/2, u.y*ch + ch/2, Math.max(3, Math.min(cw,ch)/3), 0, Math.PI*2);
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