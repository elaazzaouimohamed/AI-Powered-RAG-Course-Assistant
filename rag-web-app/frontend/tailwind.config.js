/**
 * Les palettes `gray` et `indigo` sont mappées sur des variables CSS (définies dans index.css).
 * - `gray`   : pilote le thème clair/sombre (la rampe est inversée en mode clair).
 * - `indigo` : pilote la couleur d'accent (changée par le sélecteur dans les Paramètres).
 * Résultat : tout le code existant (`bg-gray-900`, `text-indigo-400`, `bg-indigo-500/20`…)
 * devient thématisable sans toucher aux composants. `<alpha-value>` préserve les variantes /opacité.
 */
const gray = Object.fromEntries(
  [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
    .map(s => [s, `rgb(var(--g-${s}) / <alpha-value>)`])
)
const accent = Object.fromEntries(
  [300, 400, 500, 600]
    .map(s => [s, `rgb(var(--a-${s}) / <alpha-value>)`])
)

export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        gray,
        indigo: accent,   // remappe indigo -> accent
        accent,           // alias explicite (bg-accent-500, etc.)
      },
    },
  },
  plugins: [],
}
