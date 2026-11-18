// Ribbons in the spirit of the Purpose and AllSorted swooshes, flowing across the whole window
// behind the logos: stacked pairs with a white gap between them, each band swelling and thinning
// as if it twists, with a soft grey sheen. Units are the backdrop's: the window is 1000 tall and
// its right edge is x = 300, so wider windows show more of the negative x the ribbons start in.

type Ribbon = {
  y: number // centre line's resting height
  amplitude: number // how far the wave swings up and down
  wavelength: number
  phase: number
  thickness: number // widest point of the band
  twist: number // where along the band it swells and thins
  light: string // sheen: light at both ends of the window, deep in the middle
  deep: string
}

const FROM = -3200 // far enough left for very wide windows
const TO = 340 // just past the right edge
const STEP = 25

// Each pair shares one wave so its two bands run parallel, like the logos' ribbons.
const RIBBONS: Ribbon[] = [
  { y: 200, amplitude: 70, wavelength: 2200, phase: 0.6, thickness: 110, twist: 0, light: '#f7f7f7', deep: '#eeeeee' },
  { y: 320, amplitude: 70, wavelength: 2200, phase: 0.6, thickness: 100, twist: 1.3, light: '#fafafa', deep: '#f3f3f3' },
  { y: 690, amplitude: 90, wavelength: 2600, phase: 2.4, thickness: 130, twist: 0.5, light: '#f7f7f7', deep: '#eeeeee' },
  { y: 825, amplitude: 90, wavelength: 2600, phase: 2.4, thickness: 110, twist: 2, light: '#fafafa', deep: '#f3f3f3' },
]

function band(ribbon: Ribbon): string {
  const upper: string[] = []
  const lower: string[] = []
  for (let x = FROM; x <= TO; x += STEP) {
    const centre = ribbon.y + ribbon.amplitude * Math.sin((2 * Math.PI * x) / ribbon.wavelength + ribbon.phase)
    // Swells to full thickness and thins to about a third, a little faster than the wave itself.
    const half = (ribbon.thickness * (0.675 + 0.325 * Math.sin((2 * Math.PI * x) / (0.6 * ribbon.wavelength) + ribbon.twist))) / 2
    upper.push(`${x} ${(centre - half).toFixed(1)}`)
    lower.unshift(`${x} ${(centre + half).toFixed(1)}`)
  }

  return `M${upper.join('L')}L${lower.join('L')}Z`
}

const sheens = RIBBONS.map(
  (ribbon, i) =>
    `<linearGradient id="ribbon${i}" gradientUnits="userSpaceOnUse" x1="-1500" y1="0" x2="300" y2="0"><stop offset="0" stop-color="${ribbon.light}"/><stop offset="0.55" stop-color="${ribbon.deep}"/><stop offset="1" stop-color="${ribbon.light}"/></linearGradient>`,
).join('')

export const WAVES = `<defs>${sheens}</defs>${RIBBONS.map((ribbon, i) => `<path fill="url(#ribbon${i})" d="${band(ribbon)}"/>`).join('')}`
