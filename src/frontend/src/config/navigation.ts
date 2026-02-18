export interface NavLink {
  path: string;
  label: string;
  children?: NavLink[];  // For dropdown menus
  requiredRoles?: string[];  // If set, only users with at least one matching role can see this link
}

export const navigationLinks: NavLink[] = [
  {
    path: '/player',
    label: 'Player',
    requiredRoles: ['player', 'dm'],
    children: [
      { path: '/character_creator', label: 'Character Creator' },
    ]
  },
  {
    path: '/dm',
    label: 'DM',
    requiredRoles: ['dm'],
    children: [
      { path: '/encounter_builder', label: 'Encounter Builder' },
      { path: '/encounter_player', label: 'Encounter Player' },
      { path: '/map', label: 'Map' },
      { path: '/settings', label: 'Settings' },
    ]
  },
  { path: '/campaign', label: 'Campaign' },
  { path: '/homebrew', label: 'Homebrew' },
];
