/* Deterministic teaching models; no services or external dependencies. */
(() => {
  'use strict';
  const models = {
    little: (qps, ms) => qps * ms / 1000,
    queue: (incoming, capacity, seconds, initial = 0) => Math.max(0, initial + (incoming - capacity) * seconds),
    drain: (incoming, capacity, initial) => initial === 0 ? 0 : capacity > incoming ? initial / (capacity - incoming) : Infinity,
    capacity: (qps, perInstance, utilization) => Math.ceil(qps / (perInstance * utilization / 100)),
    shard: id => Number(BigInt(id) % 16n),
    skew: hot => [hot + (100 - hot) / 10, ...Array(9).fill((100 - hot) / 10)],
    wordcount: text => {
      const mapped = (text.match(/\S+/gu) || []).map(word => [word, 1]);
      const grouped = new Map();
      mapped.forEach(([word]) => grouped.set(word, [...(grouped.get(word) || []), 1]));
      return {mapped, grouped: [...grouped], reduced: [...grouped].map(([word, ones]) => [word, ones.length])};
    },
    watermark: (events, tolerance) => {
      let max = null, mark = null, sum = 0, late = 0, closed = false;
      const rows = [];
      for (const [time, amount] of events) {
        // Zero allowed lateness: reject only records for the already closed [0,10) window.
        const dropped = time < 10 && closed;
        if (dropped) late++;
        else if (time < 10) sum += amount;
        max = max === null ? time : Math.max(max, time);
        mark = max - tolerance;
        if (mark >= 10) closed = true;
        rows.push({time, amount, dropped, mark});
      }
      return {max, mark, sum, late, closed, rows};
    }
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = models;
  if (typeof document === 'undefined') return;
  const fmt = value => Number.isInteger(value) ? value.toLocaleString('zh-CN') : value.toLocaleString('zh-CN', {maximumFractionDigits: 2});
  const text = (tag, content, className) => { const e = document.createElement(tag); e.textContent = content; if (className) e.className = className; return e; };
  document.querySelectorAll('[data-lab]').forEach((root, instance) => {
    const kind = root.dataset.lab;
    const fields = document.createElement('div'); fields.className = 'lab-fields';
    const actions = document.createElement('div'); actions.className = 'lab-actions';
    const output = document.createElement('div'); output.className = 'lab-output'; output.setAttribute('role', 'status'); output.setAttribute('aria-live', 'polite');
    const note = text('p', '', 'lab-note');
    root.append(text('p', 'INTERACTIVE / 交互实验', 'eyebrow'), fields, actions, output, note);
    const defaults = [];
    const input = (label, value, min = 0, max = 10000000, step = 1, type = 'number') => {
      const wrap = document.createElement('label'); const field = document.createElement('input');
      wrap.append(text('span', label), field); field.type = type; field.value = value; field.id = `lab-${instance}-${defaults.length}`;
      if (type === 'number') { field.min = min; field.max = max; field.step = step; }
      fields.append(wrap); defaults.push([field, String(value)]); return field;
    };
    const button = (label, fn) => { const b = text('button', label); b.type = 'button'; b.addEventListener('click', fn); actions.append(b); return b; };
    const numeric = field => {
      const value = Number(field.value);
      if (field.value.trim() === '' || !Number.isFinite(value) || !field.checkValidity()) throw Error('请在输入框标示的范围内填写有效数字。');
      return value;
    };
    const show = (headline, detail = '') => { output.replaceChildren(text('strong', headline), text('p', detail)); };
    const safe = fn => () => { try { root.removeAttribute('data-invalid'); fn(); } catch (error) { root.dataset.invalid = 'true'; show('请检查输入', error.message); } };
    let update = () => {}, reset = () => {};
    const chart = (values, labels, unit = '') => {
      const list = document.createElement('div'); list.className = 'lab-chart'; list.setAttribute('aria-label', '数值对比');
      const max = Math.max(1, ...values);
      values.forEach((value, i) => {
        const row = document.createElement('div'); row.className = 'lab-bar-row';
        const bar = document.createElement('i'); bar.style.width = `${value / max * 100}%`; bar.setAttribute('aria-hidden', 'true');
        const track = document.createElement('span'); track.className = 'lab-track'; track.append(bar);
        row.append(text('small', labels[i]), track, text('b', fmt(value) + unit)); list.append(row);
      }); output.append(list);
    };
    if (kind === 'little') {
      const qps = input('吞吐量（QPS，0–1,000,000）', 1000, 0, 1000000);
      const ms = input('平均响应时间（ms，0–60,000）', 200, 0, 60000);
      update = () => show(`${fmt(models.little(numeric(qps), numeric(ms)))} 个平均在途请求`, `${fmt(numeric(qps))} × ${fmt(numeric(ms) / 1000)} 秒`);
      note.textContent = '利特尔法则的稳态示意，统计边界需一致；在途请求数不等于线程数或 CPU 核数。';
    } else if (kind === 'queue' || kind === 'lag') {
      const lag = kind === 'lag';
      const incoming = input('生产速率（条/秒，0–1,000,000）', lag ? 80000 : 1000, 0, 1000000);
      const capacity = input('消费能力（条/秒，0–1,000,000）', lag ? 100000 : 1000, 0, 1000000);
      const initial = input('初始积压（条，0–100,000,000）', lag ? 3000000 : 0, 0, 100000000);
      const duration = input('观察时长（秒，1–3,600）', lag ? 600 : 10, 1, 3600);
      update = () => {
        const a = numeric(incoming), b = numeric(capacity), q = numeric(initial), t = numeric(duration);
        const drain = models.drain(a, b, q);
        show(`${fmt(t)} 秒后积压 ${fmt(models.queue(a, b, t, q))} 条`, q === 0 ? (a > b ? '当前无积压，但持续输入将产生积压。' : '当前无积压，消费能力可以覆盖输入。') : Number.isFinite(drain) ? `理想清空时间：${fmt(drain)} 秒（${fmt(drain / 60)} 分钟）` : '持续生产下无法清空：消费能力必须大于生产速率。');
        const times = Array.from({length: 11}, (_, i) => t * i / 10);
        chart(times.map(s => models.queue(a, b, s, q)), times.map(s => `${fmt(s)}s`), ' 条');
      };
      note.textContent = '恒定速率、无限队列的理想模型，积压最低为零；不计重试、确认、网络或过期。';
    } else if (kind === 'atomic') {
      const label = document.createElement('label'); label.append(text('span', '库存扣减方式'));
      const mode = document.createElement('select'); mode.setAttribute('aria-label', '库存扣减方式');
      for (const [value, title] of [['unsafe','GET + DECR（非原子组合）'],['lua','Lua 原子检查并扣减']]) { const o = text('option', title); o.value = value; mode.append(o); }
      label.append(mode); fields.append(label); let step = 0;
      const unsafe = [['库存 1；两位用户等待领取。',''],['张三 GET → 1；通过检查。','库存仍为 1'],['李四 GET → 1；也通过检查。','库存仍为 1'],['张三 DECR → 0；领取成功。',''],['李四 DECR → −1；也领取成功。','发生超卖：两个请求的检查和扣减交错执行。']];
      const atomic = [['库存 1；两位用户等待领取。',''],['张三脚本：检查 1，再扣减至 0，领取成功。','同一个脚本执行期间，李四的命令不能穿插。'],['李四脚本：库存为 0，拒绝领取。','库存保持 0，无超卖。']];
      const next = button('下一步', safe(() => { step++; update(); }));
      update = () => { const sequence = mode.value === 'lua' ? atomic : unsafe; step = Math.min(step, sequence.length - 1); show(`步骤 ${step + 1} / ${sequence.length}：${sequence[step][0]}`, sequence[step][1]); next.disabled = step === sequence.length - 1; };
      mode.addEventListener('change', () => { step = 0; update(); }); reset = () => {step = 0; mode.value = 'unsafe';};
      note.textContent = '演示预先设定的交错顺序；Lua 原子性不等于错误回滚，也不涵盖 Redis 之外的消息或数据库操作。';
    } else if (kind === 'bucket') {
      const capacity = input('桶容量（1–1,000）', 5, 1, 1000);
      const refill = input('每次补充令牌数（1–1,000）', 1, 1, 1000);
      let tokens = 5, passed = 0, rejected = 0;
      button('发送请求', safe(() => { numeric(capacity); numeric(refill); if (tokens > 0) {tokens--; passed++;} else rejected++; update(); }));
      button('补充令牌', safe(() => {tokens = Math.min(numeric(capacity), tokens + numeric(refill)); update();}));
      update = () => { numeric(refill); tokens = Math.min(tokens, numeric(capacity)); show(`剩余令牌 ${fmt(tokens)}`, `已放行 ${fmt(passed)} · 已拒绝 ${fmt(rejected)}`); };
      reset = () => {tokens = 5; passed = rejected = 0;};
      note.textContent = '手动补充令牌以观察突发限流；生产系统通常按时间补充，本实验不启动后台计时器。';
    } else if (kind === 'pagination') {
      const offset = input('OFFSET（0–100,000,000）', 100000, 0, 100000000);
      const size = input('每页行数（1–1,000）', 20, 1, 1000);
      update = () => { const o = numeric(offset), n = numeric(size); show(`OFFSET 处理约 ${fmt(o + n)} 条；游标连续读取 ${fmt(n)} 条`, `前者跳过 ${fmt(o)} 条后取 ${n} 条。游标方式另需索引定位。`); chart([o + n, n], ['OFFSET','游标连续读取'], ' 条'); };
      note.textContent = '假设索引支持过滤与排序、无额外残余筛选。记录数不是耗时；真实查询还包括索引定位、回表和并发修改。';
    } else if (kind === 'shard') {
      const id = input('非负整数 userId（支持大整数）', '1001', 0, 0, 1, 'text'); id.inputMode = 'numeric';
      update = () => {if (!/^\d{1,40}$/.test(id.value)) throw Error('请输入 1–40 位非负整数，不支持小数或负数。'); const target = models.shard(id.value); show(`orders_${String(target).padStart(2, '0')}`, `${id.value} % 16 = ${target}`); const grid = document.createElement('div'); grid.className = 'shard-grid'; for (let i = 0; i < 16; i++) { const cell = text('span', String(i).padStart(2,'0')); if (i === target) {cell.className = 'active'; cell.setAttribute('aria-label', `目标分片 ${i}`);} grid.append(cell); } output.append(grid);};
      note.textContent = '仅演示模运算路由。扩容、热点、全局 ID 查询与数据迁移需要额外设计。';
    } else if (kind === 'wordcount') {
      const label = document.createElement('label'); label.append(text('span','输入文本（空白分词，区分大小写，最多 5,000 字符）'));
      const area = document.createElement('textarea'); area.value = 'Java Redis Java\nRedis MySQL\nJava MySQL Redis'; area.maxLength = 5000; area.rows = 4; label.append(area); fields.append(label); defaults.push([area, area.value]);
      let step = 0; const names = ['输入文件','Map 映射','Shuffle 分组','Reduce 汇总'];
      const prev = button('上一步', () => {step = Math.max(0,step - 1); update();});
      const next = button('下一步', () => {step = Math.min(3,step + 1); update();});
      update = () => {if (area.value.length > 5000) throw Error('文本不能超过 5,000 字符。'); const result = models.wordcount(area.value); show(`${step + 1} / 4 · ${names[step]}`); const pre = document.createElement('pre'); pre.textContent = step === 0 ? area.value || '（空输入）' : JSON.stringify([null,result.mapped,result.grouped,result.reduced][step], null, 2); output.append(pre); prev.disabled = step === 0; next.disabled = step === 3;};
      reset = () => {step = 0;}; note.textContent = '逐步展示键值对变换。真实框架还负责分区、排序、调度、文件管理和失败重试。';
    } else if (kind === 'skew') {
      const hot = input('热点 Key 占比（0–100%）', 80, 0, 100);
      update = () => {const loads = models.skew(numeric(hot)); show(`热点 Reducer 负载 ${fmt(loads[0])}%`, `其他各 ${fmt(loads[1])}%。剩余数据均匀分配给全部十个 Reducer。`); chart(loads, loads.map((_,i) => `Reducer ${i + 1}`), '%');};
      note.textContent = '热点 Key 固定进入第一个 Reducer。负载为记录占比，未考虑不同记录的大小和处理成本。';
    } else if (kind === 'watermark') {
      const tolerance = input('乱序容忍时间（秒，0–30）', 5, 0, 30);
      const events = [[2,100],[8,200],[5,50],[17,150],[9,80],[25,300]]; let count = 0;
      const next = button('接收下一条事件', safe(() => {numeric(tolerance); count = Math.min(events.length, count + 1); update();}));
      update = () => {const state = models.watermark(events.slice(0,count), numeric(tolerance)); show(`最大事件时间 ${state.max === null ? '—' : state.max + 's'} · Watermark ${state.mark === null ? '—' : state.mark + 's'}`, `[0,10) 窗口金额 ¥${state.sum} · 窗口关闭后被丢弃 ${state.late} 条 · ${state.closed ? '窗口已触发并关闭' : '窗口等待时间推进'}`); const list = document.createElement('ol'); events.forEach(([time,amount], i) => list.append(text('li', `${time}s · ¥${amount} · ${i >= count ? '待到达' : state.rows[i].dropped ? '窗口已关闭，丢弃' : '已接收'}`))); output.append(list); next.disabled = count === events.length; tolerance.disabled = count > 0;};
      reset = () => {count = 0; tolerance.disabled = false;};
      note.textContent = '单输入秒级模型，Watermark≈最大事件时间−容忍时间；零 allowed lateness。真实 Flink 还涉及毫秒边界、周期发射、输入最小值和空闲分区。开始接收后需重置才能修改策略。';
    } else if (kind === 'capacity') {
      const qps = input('目标峰值 QPS（0–10,000,000）', 100000);
      const throughput = input('单实例稳定吞吐 QPS（1–1,000,000）', 2000, 1, 1000000);
      const utilization = input('规划负载比例（1–100%）', 70, 1, 100);
      update = () => show(`${fmt(models.capacity(numeric(qps), numeric(throughput), numeric(utilization)))} 台 API 实例`, `ceil(${fmt(numeric(qps))} ÷ (${fmt(numeric(throughput))} × ${numeric(utilization)}%))`);
      note.textContent = '假设同质实例且负载均匀，无其他共享瓶颈；尚未计入可用区故障、扩容延迟及连接资源。';
    } else {show('该实验暂不可用'); return;}
    const run = safe(update);
    fields.addEventListener('input', run);
    button('重置实验', () => {defaults.forEach(([field,value]) => {field.value = value;}); reset(); run();});
    run();
  });
})();
