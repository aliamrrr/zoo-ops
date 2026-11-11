import { api } from "./api.js";
import { critterCanvas } from "./art.js";
import { Sfx } from "./audio.js";
import { Dock } from "./dock.js";
import { Game } from "./game.js";
import { Stations } from "./stations.js";
import { World } from "./world.js";

const $ = (selector) => document.querySelector(selector);

function showTab(name) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.setAttribute("aria-selected", String(tab.dataset.tab === name));
  });
  $("#panel-play").hidden = name !== "play";
  $("#panel-stations").hidden = name !== "stations";
}

async function boot() {
  $("#brand-face").append(critterCanvas("owl", 36, { face: true }));
  const sfx = new Sfx();
  const [levels, questions] = await Promise.all([api.levels(), api.questions()]);
  const stations = new Stations(levels);

  let game = null;
  const openStation = (id) => {
    game.pause();
    showTab("stations");
    stations.open(id);
  };
  const dock = new Dock($("#dock"), openStation);
  game = new Game({
    questions,
    onOpenStation: openStation,
    onMoment: (id, good, stat) => dock.pulse(id, good, stat),
    onShiftStart: () => {
      sfx.unlock();
      dock.reset();
    },
  });
  new World(game, $("#world"), sfx);

  const sound = $("#sound");
  sound.dataset.muted = String(sfx.muted);
  sound.addEventListener("click", () => {
    sfx.unlock();
    sound.dataset.muted = String(sfx.toggle());
  });

  let checking = false;
  async function checkSystems() {
    if (checking) return;
    checking = true;
    try {
      const systems = await api.systems();
      game.setSystems(systems);
      stations.update(systems);
      dock.update(systems);
    } finally {
      checking = false;
    }
  }

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      if (tab.dataset.tab === "stations") game.pause();
      showTab(tab.dataset.tab);
    });
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) game.pause();
  });
  window.addEventListener("focus", checkSystems);

  await checkSystems();
}

boot();
