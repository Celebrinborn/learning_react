export interface NavLink {
  path: string;
  label: string;
  children?: NavLink[];  // For dropdown menus
}

export const navigationLinks: NavLink[] = [
  { 
    path: '/player', 
    label: 'Player',
    children: [
      { path: '/character_creator', label: 'Character Creator' },
    ]
  },
  { 
    path: '/dm', 
    label: 'DM',
    children: [
      { path: '/encounter_builder', label: 'Encounter Builder' },
      { path: '/encounter_player', label: 'Encounter Player' },
      { path: '/settings', label: 'Settings' },
    ]
  },
  { path: '/campaign', label: 'Campaign' },
];
