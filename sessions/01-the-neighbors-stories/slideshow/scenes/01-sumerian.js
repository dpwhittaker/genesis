/* Scene 1 — Sumer: Enlil separates An (heaven) and Ki (earth).
   Art is a generated still + video:
     - Enlil_An_and_Ki.jpeg — Enlil (winged marble) at right swings his hoe at
       center, striking the seam between the lapis dome of heaven (An, upper-left)
       and the gold drum of earth (Ki, lower-left).
     - Enlil_separates_An_and_Ki.mp4 — the separation, played when the hoe is tapped.
   Tap An/Ki/Enlil to magnify + read; tap the glowing hoe to play the clip. */
window.SLIDESHOW.registerScene({
  id: 'sumerian',
  title: 'Sumer — Enlil separates Heaven and Earth',
  source: 'Song of the Hoe · Gilgameš, Enkidu and the Nether World (ETCSL)',
  hint: 'Tap An, Ki, or Enlil to learn who they are — tap the glowing hoe to watch the separation.',

  svg: `
    <image href="assets/Enlil_An_and_Ki.jpeg" x="0" y="0" width="1920" height="1080"
           preserveAspectRatio="xMidYMid slice"/>
    <rect x="0" y="0" width="1920" height="1080" fill="url(#vig)" pointer-events="none"/>
    <defs><radialGradient id="vig" cx="50%" cy="46%" r="75%">
      <stop offset="64%" stop-color="#000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0.45"/>
    </radialGradient></defs>
  `,

  entities: [
    {
      id: 'an', label: 'An — Heaven', point: [470, 260], labelXY: [330, 120],
      focus: [110, 60, 880, 495],
      text: `<span class="tag">The sky</span>
        <p><b>An</b> is heaven itself — the oldest, highest god of the Sumerian world, the
        sky-father from whom the other gods descend. In the beginning he is not <i>above</i> the
        earth but fused <i>to</i> it: heaven and earth are one mass, with no room between them for
        anything to live.</p>`,
    },
    {
      id: 'ki', label: 'Ki — Earth', point: [470, 790], labelXY: [330, 980],
      focus: [120, 540, 860, 484],
      text: `<span class="tag">The earth</span>
        <p><b>Ki</b> is the earth, An's counterpart — together <i>An-Ki</i> ("heaven-earth") is the
        Sumerian word for the whole cosmos. While the two are pressed together nothing can grow or
        breathe; creation cannot begin until they are parted.</p>`,
    },
    {
      id: 'enlil', label: 'Enlil — Lord Wind', point: [1480, 380], labelXY: [1650, 180],
      focus: [1100, 70, 800, 600],
      text: `<span class="tag">Lord of the air</span>
        <p><b>Enlil</b> means "Lord <i>Lil</i>" — lord of <i>air, wind, breath</i>. Son of An and
        Ki, born in the seam between them, it is his nature — moving air — that forces heaven and
        earth apart and then fills the space between.</p>
        <div class="gen"><b>Genesis echo:</b> before the first "Let there be," a <b>rûaḥ</b> — wind,
        breath, Spirit — moves over the waters (Gen 1:2). The very thing that pries the cosmos open
        in Sumer is there in Genesis too, but tamed: it simply hovers, and waits on God's word.</div>`,
    },
    {
      id: 'sep', label: '▸ The Hoe — separate them', point: [880, 470], labelXY: [900, 910],
      action: 'separation', labelSize: 30,
      panelTitle: 'Creation as separation',
      text: `<span class="tag">What just happened</span>
        <p>With the hoe, Enlil drives a wedge into the fused mass and <b>pries heaven up off the
        earth</b>, then holds them apart. The world is not made from nothing; it is made by
        <b>splitting</b> what was one into an <i>above</i> and a <i>below</i>, with breathing room
        between.</p>
        <div class="gen"><b>Genesis answers:</b> Genesis 1 keeps this very architecture — and uses
        the matching Hebrew verb <b>bāḏal</b>, "to divide," five times: light from dark, the waters
        above from the waters below, day from night. The picture is the neighbors' picture, but the
        violence is gone: only God, <b>separating by his word</b>, calling each division <i>good</i>.</div>`,
    },
  ],

  animations: {
    // the generated separation clip plays, then the panel explains it
    separation: { type: 'video', href: 'assets/Enlil_separates_An_and_Ki.mp4' },
  },
});
