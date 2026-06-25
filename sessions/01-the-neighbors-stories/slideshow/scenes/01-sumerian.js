/* Scene 1 — Sumer: Enlil separates Heaven (An) from Earth (Ki) with the hoe.
   Source: the Song of the Hoe; Gilgameš, Enkidu and the Nether World (ETCSL).

   Initial state: An (sky) and Ki (earth) are one fused mass; Enlil stands aside
   with the hoe. Tapping a god magnifies it + describes it. Tapping the hoe plays
   the separation: Enlil wedges in, pries heaven up and earth down, then rises
   into the gap to hold them apart — then the panel explains it. */
window.SLIDESHOW.registerScene({
  id: 'sumerian',
  title: 'Sumer — Enlil pries Heaven and Earth apart',
  source: 'Song of the Hoe · Gilgameš, Enkidu and the Nether World (ETCSL)',
  hint: 'Tap An, Ki, or Enlil to learn who they are — tap the glowing Hoe to watch creation happen.',
  resetClasses: ['sep-1', 'sep-2', 'sep-3'],

  svg: `
    <defs>
      <radialGradient id="void" cx="50%" cy="42%" r="75%">
        <stop offset="0%" stop-color="#161d33"/><stop offset="100%" stop-color="#05070d"/>
      </radialGradient>
      <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#1b2a6b"/><stop offset="100%" stop-color="#2a3f86"/>
      </linearGradient>
      <linearGradient id="landGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#7a5a2e"/><stop offset="55%" stop-color="#5e4321"/><stop offset="100%" stop-color="#3c2c16"/>
      </linearGradient>
    </defs>

    <rect class="bg" x="0" y="0" width="1920" height="1080" fill="url(#void)"/>
    <g class="bgstars" fill="#8b96c8">
      <circle cx="180" cy="160" r="2.5"/><circle cx="320" cy="90" r="2"/><circle cx="1650" cy="120" r="2.5"/>
      <circle cx="1780" cy="240" r="2"/><circle cx="120" cy="420" r="2"/><circle cx="1820" cy="520" r="2.5"/>
      <circle cx="90" cy="650" r="2"/><circle cx="1700" cy="700" r="2"/>
    </g>

    <!-- AN — the heavens (a starry dome) -->
    <g id="an" class="ent">
      <path class="sky" d="M360 560 A600 470 0 0 1 1560 560 Z" fill="url(#skyGrad)" stroke="#9fb0ff" stroke-width="3" stroke-opacity="0.5"/>
      <g fill="#dbe3ff">
        <circle cx="700" cy="360" r="4"/><circle cx="850" cy="250" r="3"/><circle cx="1020" cy="200" r="5"/>
        <circle cx="1180" cy="270" r="3.5"/><circle cx="1300" cy="380" r="4"/><circle cx="980" cy="330" r="3"/>
        <circle cx="600" cy="470" r="3"/><circle cx="1380" cy="470" r="3"/>
      </g>
      <circle class="sun" cx="1280" cy="430" r="40" fill="#f4d774"/>
      <path class="moon" d="M690 450 a44 44 0 1 0 10 -70 a34 34 0 1 1 -10 70 z" fill="#e7ecff"/>
    </g>

    <!-- KI — the earth -->
    <g id="ki" class="ent">
      <path class="land" d="M300 560 L1620 560 L1560 1040 L360 1040 Z" fill="url(#landGrad)" stroke="#3c2c16" stroke-width="3"/>
      <g stroke="#3f2e17" stroke-width="3" stroke-opacity="0.6">
        <path d="M430 660 Q960 700 1490 660"/><path d="M410 760 Q960 810 1510 760"/><path d="M395 870 Q960 925 1525 870"/>
      </g>
      <g fill="#2f7d46"><path d="M620 560 q-18 -70 6 -120 q24 50 6 120 z"/><path d="M1300 560 q-16 -64 4 -110 q22 46 6 110 z"/></g>
    </g>

    <!-- the gap / air revealed between them when split (Enlil's domain) -->

    <!-- ENLIL — Lord Wind, with the hoe -->
    <g id="enlil" class="ent">
      <g id="enlil-arm-l"><path d="M430 690 q-70 30 -86 110" stroke="#caa86a" stroke-width="26" fill="none" stroke-linecap="round"/></g>
      <g id="enlil-arm-r"><path d="M540 690 q70 24 92 92" stroke="#caa86a" stroke-width="26" fill="none" stroke-linecap="round"/></g>
      <path class="robe" d="M430 690 q55 -34 110 0 l44 250 l-198 0 z" fill="#b98f4f" stroke="#7a5a2e" stroke-width="3"/>
      <g stroke="#8a6736" stroke-width="3" stroke-opacity="0.6"><path d="M404 800 h182"/><path d="M396 860 h198"/></g>
      <rect x="470" y="560" width="30" height="150" fill="#caa86a"/>
      <circle class="head" cx="485" cy="556" r="40" fill="#e7c896" stroke="#7a5a2e" stroke-width="3"/>
      <path class="beard" d="M455 576 q30 60 60 0 q-6 56 -30 64 q-24 -8 -30 -64 z" fill="#6b4f2a"/>
      <!-- horned crown of divinity -->
      <path class="crown" d="M455 524 q30 -26 60 0 z" fill="#d9b777"/>
      <path d="M460 520 q-26 -6 -34 -28 q22 6 38 22 z M510 520 q26 -6 34 -28 q-22 6 -38 22 z" fill="#d9b777"/>
    </g>

    <!-- THE HOE (al) -->
    <g id="hoe" class="ent">
      <line x1="556" y1="700" x2="700" y2="540" stroke="#7a5836" stroke-width="14" stroke-linecap="round"/>
      <path d="M690 528 l46 -16 l10 34 l-44 18 z" fill="#9aa3ad" stroke="#5c6770" stroke-width="3"/>
    </g>

    <!-- wind streaks shown while Enlil holds heaven and earth apart -->
    <g id="wind" class="fx" opacity="0">
      <path d="M700 540 q160 -30 320 0" stroke="#bcd0ff" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.8"/>
      <path d="M760 620 q200 -34 400 0" stroke="#bcd0ff" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.6"/>
      <path d="M720 700 q180 28 360 0" stroke="#bcd0ff" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.6"/>
    </g>
  `,

  css: `
    #an, #ki, #enlil, #hoe, #wind, #enlil-arm-l, #enlil-arm-r {
      transition: transform 1.05s cubic-bezier(.22,.7,.18,1), opacity .8s; }
    #enlil-arm-l, #enlil-arm-r { transform-box: fill-box; }
    #enlil-arm-l { transform-origin: 92% 8%; } #enlil-arm-r { transform-origin: 8% 8%; }
    /* magnify dimming */
    .camera.has-focus .ent { opacity: .28; transition: opacity .5s; }
    .camera.has-focus .ent.lit { opacity: 1; }

    /* --- separation timeline (driven by #stage classes) --- */
    #stage.sep-1 #enlil { transform: translate(250px, -30px); }
    #stage.sep-1 #hoe   { transform: translate(250px, -30px) rotate(-14deg); transform-origin: 600px 700px; }

    #stage.sep-2 #an    { transform: translateY(-250px); }
    #stage.sep-2 #ki    { transform: translateY(170px); }
    #stage.sep-2 #enlil { transform: translate(330px, -40px); }
    #stage.sep-2 #hoe   { transform: translate(330px, -150px) rotate(-32deg); transform-origin: 600px 700px; }

    #stage.sep-3 #an    { transform: translateY(-250px); }
    #stage.sep-3 #ki    { transform: translateY(170px); }
    #stage.sep-3 #enlil { transform: translate(470px, -150px); }
    #stage.sep-3 #enlil #enlil-arm-l { transform: rotate(-128deg); }
    #stage.sep-3 #enlil #enlil-arm-r { transform: rotate(128deg); }
    #stage.sep-3 #hoe   { opacity: 0; }
    #stage.sep-3 #wind  { opacity: 1; }
  `,

  entities: [
    {
      id: 'an', svgId: 'an', label: 'An — Heaven', point: [1150, 300], labelXY: [1500, 180],
      focus: [410, 30, 1100, 619],
      text: `<span class="tag">The sky</span>
        <p><b>An</b> is heaven itself — and the oldest, highest god of the Sumerian world, the
        sky-father from whom the other gods descend.</p>
        <p>In the beginning An is not <i>above</i> the earth; he is fused <i>to</i> it. Heaven and
        earth are one mountain, with no air, no light, no room between them for anything to live.</p>`,
    },
    {
      id: 'ki', svgId: 'ki', label: 'Ki — Earth', point: [1100, 800], labelXY: [1500, 930],
      focus: [410, 470, 1100, 619],
      text: `<span class="tag">The earth</span>
        <p><b>Ki</b> is the earth — paired with An as his counterpart. Together <i>An-Ki</i>
        ("heaven-earth") is the Sumerian word for the whole cosmos.</p>
        <p>While the two are pressed together there is nowhere for grain to grow or breath to
        move. Creation cannot begin until they are parted.</p>`,
    },
    {
      id: 'enlil', svgId: 'enlil', label: 'Enlil — Lord Wind', point: [486, 600], labelXY: [250, 430],
      focus: [120, 470, 800, 450],
      text: `<span class="tag">Lord of the air</span>
        <p><b>Enlil</b> means "Lord <i>Lil</i>" — lord of <i>air, wind, breath</i>. He is the son
        of An and Ki, born in the seam between them, and it is his nature — moving air — that
        forces heaven and earth apart and then fills the space between.</p>
        <div class="gen"><b>Genesis echo:</b> before the first "Let there be," a <b>rûaḥ</b> — wind,
        breath, Spirit — moves over the waters (Gen 1:2). The very thing that pries the cosmos open
        in Sumer is there in Genesis too, but tamed: it simply hovers, and waits on God's word.</div>`,
    },
    {
      id: 'hoe', svgId: 'hoe', label: '▸ The Hoe — separate them', point: [640, 600], labelXY: [250, 760],
      action: 'separation', labelSize: 30,
      panelTitle: 'Creation as separation',
      text: `<span class="tag">What just happened</span>
        <p>With the <b>hoe</b>, Enlil drives a wedge into the fused mass and <b>pries heaven up off
        the earth</b> — then rushes into the gap and holds them apart. The world is not made from
        nothing; it is made by <b>splitting</b> what was one into an <i>above</i> and a <i>below</i>,
        with breathing room in between.</p>
        <div class="gen"><b>Genesis answers:</b> Genesis 1 keeps this very architecture — and uses the
        matching Hebrew verb <b>bāḏal</b>, "to divide," five times: light from dark, the waters above
        from the waters below, day from night. The picture is the neighbors' picture — an above and a
        below, parted to make room for life — but the violence is gone. No struggle, no wedge, no
        straining god: only God, <b>separating by his word</b>, and calling each division <i>good</i>.</div>`,
    },
  ],

  animations: {
    async separation(api) {
      api.add('sep-1');  await api.wait(820);     // Enlil steps in, hoe raised
      api.add('sep-2');  await api.wait(1100);    // the wedge: heaven up, earth down
      api.add('sep-3');  await api.wait(1000);    // Enlil rises into the gap, holds them apart, wind stirs
      await api.tween([520, 120, 880, 495], 700); // settle the camera on the held-open world
    },
  },
});
