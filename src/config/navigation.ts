export interface NavLink {
  path: string;
  label: string;
}

export const navigationLinks: NavLink[] = [
  { path: '/', label: 'Home' },
  { path: '/character_creator', label: 'Character Creator' },
  { path: '/campaign', label: 'Campaign' },
  { path: '/settings', label: 'Settings' },
];
