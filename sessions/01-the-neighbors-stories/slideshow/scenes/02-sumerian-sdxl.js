/* Scene 2 — the SAME Sumerian narrative as scene 1, but the art is an SDXL-painted
   image and the signature animation is a WAN image-to-video clip. Built to sit
   beside the vector scene so the two approaches can be compared directly.

   The engine is unchanged: the painted scene is a raster <image> filling the
   camera's viewBox, so the existing viewBox-tween magnify zooms into it; the
   separation is wired through the {type:'video'} animation hook. Until the WAN
   clip is generated, the action falls back to a cinematic camera push so the
   scene is fully usable. Magnify regions are matched to the chosen image. */
window.SLIDESHOW.registerScene({
  id: 'sumerian-sdxl',
  title: 'Sumer — the same scene, painted (SDXL + WAN)',
  source: 'Song of the Hoe · Gilgameš, Enkidu and the Nether World (ETCSL) — art: SDXL / WAN',
  hint: 'Same story, painted. Tap An, Ki, or Enlil — tap the glowing one to watch the separation.',

  // The SDXL painting is the whole scene; the camera zooms into it for magnify.
  svg: `
    <image href="assets/sumerian-scene.png" x="0" y="0" width="1920" height="1080"
           preserveAspectRatio="xMidYMid slice"/>
    <!-- gentle vignette so the labels stay legible over the art -->
    <rect x="0" y="0" width="1920" height="1080" fill="url(#vig)" pointer-events="none"/>
    <defs><radialGradient id="vig" cx="50%" cy="46%" r="72%">
      <stop offset="60%" stop-color="#000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0.45"/>
    </radialGradient></defs>
  `,

  // regions refined to the chosen image (see assets/sumerian-scene.png)
  entities: [
    {
      id: 'an', label: 'An — Heaven', point: [960, 230], labelXY: [1480, 150],
      focus: [330, 0, 1260, 709],
      text: `<span class="tag">The sky</span>
        <p><b>An</b> is heaven itself — the oldest, highest god of the Sumerian world, the
        sky-father from whom the other gods descend. In the beginning he is not <i>above</i> the
        earth but fused <i>to</i> it: heaven and earth are one mountain, with no room between
        them for anything to live.</p>`,
    },
    {
      id: 'ki', label: 'Ki — Earth', point: [960, 880], labelXY: [1480, 950],
      focus: [330, 371, 1260, 709],
      text: `<span class="tag">The earth</span>
        <p><b>Ki</b> is the earth, An's counterpart — together <i>An-Ki</i> ("heaven-earth") is
        the Sumerian word for the whole cosmos. While the two are pressed together nothing can
        grow or breathe; creation cannot begin until they are parted.</p>`,
    },
    {
      id: 'enlil', label: 'Enlil — Lord Wind', point: [360, 560], labelXY: [820, 360],
      focus: [40, 320, 800, 450],
      text: `<span class="tag">Lord of the air</span>
        <p><b>Enlil</b> means "Lord <i>Lil</i>" — lord of <i>air, wind, breath</i>. Son of An and
        Ki, born in the seam between them, it is his nature — moving air — that forces heaven and
        earth apart and then fills the space between.</p>
        <div class="gen"><b>Genesis echo:</b> before the first "Let there be," a <b>rûaḥ</b> —
        wind, breath, Spirit — moves over the waters (Gen 1:2). The very thing that pries the
        cosmos open in Sumer is there in Genesis too, but tamed: it simply hovers, and waits on
        God's word.</div>`,
    },
    {
      id: 'sep', label: '▸ Watch the separation', point: [560, 540], labelXY: [300, 760],
      action: 'separation', labelSize: 30,
      panelTitle: 'Creation as separation',
      text: `<span class="tag">What just happened</span>
        <p>Enlil drives a wedge into the fused mass and <b>pries heaven up off the earth</b>, then
        rushes into the gap and holds them apart. The world is not made from nothing; it is made
        by <b>splitting</b> what was one into an <i>above</i> and a <i>below</i>, with breathing
        room between.</p>
        <div class="gen"><b>Genesis answers:</b> Genesis 1 keeps this very architecture — and uses
        the matching Hebrew verb <b>bāḏal</b>, "to divide," five times: light from dark, the waters
        above from the waters below, day from night. The picture is the neighbors' picture, but the
        violence is gone: only God, <b>separating by his word</b>, calling each division <i>good</i>.</div>`,
    },
  ],

  animations: {
    // When the WAN clip exists, swap this whole function for the one-liner:
    //   separation: { type: 'video', href: 'assets/sumerian-separation.mp4' },
    async separation(api) {
      await api.tween([620, 250, 700, 394], 2600);   // cinematic push toward the opening gap
    },
  },
});
