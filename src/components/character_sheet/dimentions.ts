/**
 * Structural dimension constants for the character sheet layout.
 * Sizes are based on a printable US letter width (720px).
 */

/** Box width presets based on printable letter width (720px) */
export const BoxWidth = {
  /** Small box width (80px / 1/9 of a letter paper) */
  smallBox: 80,
  /** Double box width (160px / 2/9 of a letter paper) */
  doubleBox: 160,
  /** Triple box width (240px / 3/9 of a letter paper) */
  tripleBox: 240,
  /** Full printable letter width (720px) */
  full: 720,
} as const;
