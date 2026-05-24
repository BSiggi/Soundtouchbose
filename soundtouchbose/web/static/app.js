async function load() {
  const devices = await fetch('/api/devices').then((response) => response.json());
  const zones = await fetch('/api/zones').then((response) => response.json());
  const deviceContainer = document.getElementById('devices');
  const zoneContainer = document.getElementById('zones');
  deviceContainer.innerHTML = '';
  zoneContainer.innerHTML = '';
  for (const device of devices) {
    const card = document.createElement('div');
    card.className = 'card';
    const presets = Object.keys(device.presets || {}).sort();
    card.innerHTML = `<h3>${device.name}</h3><p>${device.ip_address}</p><div class="preset-grid"></div><button data-action="playpause">Play/Pause</button><input type="range" min="0" max="100" value="20">`;
    const grid = card.querySelector('.preset-grid');
    for (let i = 1; i <= 6; i += 1) {
      const button = document.createElement('button');
      button.textContent = device.presets?.[String(i)]?.name || `Preset ${i}`;
      button.onclick = () => fetch(`/api/devices/${device.ip_address}/preset/${i}`, { method: 'POST' });
      grid.appendChild(button);
    }
    card.querySelector('[data-action="playpause"]').onclick = () => fetch(`/api/devices/${device.ip_address}/playpause`, { method: 'POST' });
    card.querySelector('input').onchange = (event) => fetch(`/api/devices/${device.ip_address}/volume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ volume: Number(event.target.value) }),
    });
    deviceContainer.appendChild(card);
  }
  for (const zone of zones) {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `<h3>${zone.name}</h3><p>Master: ${zone.master_ip}</p><button>Aktivieren</button>`;
    card.querySelector('button').onclick = () => fetch(`/api/zones/${zone.name}/activate`, { method: 'POST' });
    zoneContainer.appendChild(card);
  }
}
load();
setInterval(load, 15000);
