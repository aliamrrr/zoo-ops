import { api, useMode } from "./api.js";
import { critterCanvas } from "./art.js";
import { Sfx } from "./audio.js";
import { BlueprintEditor } from "./blueprint.js";
import { Dock } from "./dock.js";
import { Game } from "./game.js";
import { CLASSIC, readMode, switchMode } from "./mode.js";
import { Stations } from "./stations.js";
import { applyMode } from "./systems.js";
import { World } from "./world.js";

const $ = (selector) => document.querySelector(selector);
const PANELS = ["play", "stations", "blueprint"];
const RECHECK_MS = 3000;

function showTab(name) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.setAttribute("aria-selected", String(tab.dataset.tab === name));
  });
  for (const panel of PANELS) $(`#panel-${panel}`).hidden = panel !== name;
}

async function boot() {
  $("#brand-face").append(critterCanvas("owl", 36, { face: true }));
  const modes = await api.modes();
  const mode = modes.find((item) => item.key === readMode(modes.map((item) => item.key)));
  useMode(mode.key);
  applyMode(mode);
  document.title = mode.title;
  $("#brand-name").textContent = mode.title;
  document.body.dataset.mode = mode.key;

  const sfx = new Sfx();
  const [levels, questions] = await Promise.all([api.levels(), api.questions()]);

  let game = null;
  let checkSystems = () => {};
  const openTab = (name) => {
    if (name !== "play") game.pause();
    showTab(name);
  };
  const stations = new Stations(levels, mode, { onOpenBlueprint: () => openTab("blueprint") });
  const openStation = (id) => {
    openTab("stations");
    stations.open(id);
  };
  const dock = new Dock($("#dock"), openStation);
  game = new Game({
    questions,
    mode,
    modes,
    onSwitchMode: switchMode,
    onOpenStation: openStation,
    onMoment: (id, good, stat) => dock.pulse(id, good, stat),
    onShiftStart: () => {
      sfx.unlock();
      dock.reset();
    },
  });
  new World(game, $("#world"), sfx);

  if (mode.key !== CLASSIC) {
    $("#tab-blueprint").hidden = false;
    const editor = new BlueprintEditor($("#blueprint"), {
      onChecked: (progress) => {
        $("#blueprint-count").textContent = `${progress.correct}/${progress.total}`;
        checkSystems();
      },
    });
    editor.load().then((progress) => {
      $("#blueprint-count").textContent = `${progress.correct}/${progress.total}`;
    }).catch((error) => {
      $("#blueprint").textContent = `The blueprint could not load: ${error.message}`;
    });
  }

  const sound = $("#sound");
  sound.dataset.muted = String(sfx.muted);
  sound.addEventListener("click", () => {
    sfx.unlock();
    sound.dataset.muted = String(sfx.toggle());
  });

  let checking = false;
  let recheck = null;
  checkSystems = async () => {
    if (checking) return;
    checking = true;
    clearTimeout(recheck);
    try {
      const systems = await api.systems();
      game.setSystems(systems);
      stations.update(systems);
      dock.update(systems);
      if (Object.values(systems).some((system) => system.checking)) {
        recheck = setTimeout(checkSystems, RECHECK_MS);
      }
    } finally {
      checking = false;
    }
  };

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => openTab(tab.dataset.tab));
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) game.pause();
  });
  window.addEventListener("focus", checkSystems);

  await checkSystems();
}

boot();
