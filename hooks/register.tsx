import type { Register } from 'claude-code'

import { LOGOS } from './logos'
import { WAVES } from './waves'

// The scene is a strip 300 wide by 1000 tall pinned to the window's right edge, centred top to
// bottom (xMaxYMid meet), so the window's height is always 1000 units and the logos keep right.
// They stand in one column, top to bottom in ORDER, centred halfway down the window, every logo
// drawn LOGO_WIDTH wide (its height follows its own shape) with GAP between them. A compact logo
// that would stand taller than MAX_HEIGHT (Frameworks) is shrunk to it and centred instead.
const STRIP = 300
const MARGIN = 25
const LOGO_WIDTH = 100
const MAX_HEIGHT = 60
const GAP = 14
const LEFT = STRIP - MARGIN - LOGO_WIDTH

// Top-to-bottom order by name, kept apart from logos.ts so re-tracing never undoes it. A name
// left out (or misspelt) is simply not drawn.
const ORDER = [
  'Signtech',
  'Signtech Media',
  'Sarre & Company',
  'Frameworks',
  'Assured Property Management',
  'TPM Co',
  'Maillard & Co',
  'Rowlands',
  'Purpose',
  'AllSorted',
]
// Touches by name: `opacity` lightens a logo against the white ground (every logo's ink is
// already one grey, INK in tools/trace.py). Empty while every logo matches.
const TWEAKS: Record<string, { opacity?: number }> = {}
const SHOWN = ORDER.flatMap(name => LOGOS.filter(logo => logo.name === name)).map(logo => {
  const scale = Math.min(LOGO_WIDTH / logo.width, MAX_HEIGHT / logo.height)

  return {
    ...logo,
    scale,
    drawnWidth: logo.width * scale,
    drawnHeight: logo.height * scale,
    opacity: TWEAKS[logo.name]?.opacity ?? 1,
  }
})

let top = (1000 - SHOWN.reduce((sum, logo) => sum + logo.drawnHeight, 0) - GAP * (SHOWN.length - 1)) / 2
const column = SHOWN.map(logo => {
  const placed = `<g transform="translate(${LEFT + (LOGO_WIDTH - logo.drawnWidth) / 2} ${top}) scale(${logo.scale})" opacity="${logo.opacity}">${logo.svg}</g>`
  top += logo.drawnHeight + GAP

  return placed
}).join('')

// The white rect reaches well past the strip so it fills the rest of the window too; the
// ribbons flow across all of it, and the logos sit on top.
const SCENE = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${STRIP} 1000" preserveAspectRatio="xMaxYMid meet"><rect x="-20000" y="-1000" width="40000" height="3000" fill="#ffffff"/>${WAVES}${column}</svg>`

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    // A drawn scene takes glass: no blur and see-through panels, so the ground shows.
    const set = await $.theme.set({ backdrop: { scene: 'businesses', glass: { blur: 0, opacity: 0.4 } } })
    // Speak up only on failure; undefined clears the line.
    $.ui.status(set.isDrawn ? undefined : `Businesses backdrop not drawn: ${set.reason}`)

    return next(e)
  })

  on('ui.render', { component: 'Backdrop' }, ($, e, next) => {
    if (e.surface !== 'desktop' && e.surface !== 'mobile') {
      return next(e)
    }
    const { Svg } = $.ui.resolve(e)

    return <Svg source={SCENE} alt={`Logos: ${SHOWN.map(logo => logo.name).join(', ')}`} isInteractive />
  })
}
