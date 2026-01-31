// Location type constants
export const LocationType = {
  // Settlements (by size)
  CITY: 'city',
  TOWN: 'town',
  VILLAGE: 'village',
  HAMLET: 'hamlet',
  HOMESTEAD: 'homestead',
  
  // Points of Interest
  CASTLE: 'castle',
  FORTRESS: 'fortress',
  RUINS: 'ruins',
  TEMPLE: 'temple',
  SHRINE: 'shrine',
  DUNGEON: 'dungeon',
  CAVE: 'cave',
  MINE: 'mine',
  
  // Geographic Features
  MOUNTAIN_PASS: 'mountain_pass',
  BRIDGE: 'bridge',
  FORD: 'ford',
  PORT: 'port',
  
  // Events/Locations
  BATTLEFIELD: 'battlefield',
  CAMP: 'camp',
  INN: 'inn',
  TAVERN: 'tavern',
  LANDMARK: 'landmark',
  
  // Quest Related
  QUEST_LOCATION: 'quest_location',
  DANGER_ZONE: 'danger_zone',
  
  // Generic
  OTHER: 'other',
} as const;

export type LocationType = typeof LocationType[keyof typeof LocationType];

export const LocationTypeLabels: Record<LocationType, string> = {
  [LocationType.CITY]: '🏛️ City',
  [LocationType.TOWN]: '🏘️ Town',
  [LocationType.VILLAGE]: '🏡 Village',
  [LocationType.HAMLET]: '🏠 Hamlet',
  [LocationType.HOMESTEAD]: '🏚️ Homestead',
  
  [LocationType.CASTLE]: '🏰 Castle',
  [LocationType.FORTRESS]: '⛩️ Fortress',
  [LocationType.RUINS]: '🗿 Ruins',
  [LocationType.TEMPLE]: '🛕 Temple',
  [LocationType.SHRINE]: '⛩️ Shrine',
  [LocationType.DUNGEON]: '🕳️ Dungeon',
  [LocationType.CAVE]: '🕳️ Cave',
  [LocationType.MINE]: '⛏️ Mine',
  
  [LocationType.MOUNTAIN_PASS]: '🏔️ Mountain Pass',
  [LocationType.BRIDGE]: '🌉 Bridge',
  [LocationType.FORD]: '〰️ Ford',
  [LocationType.PORT]: '⚓ Port',
  
  [LocationType.BATTLEFIELD]: '⚔️ Battlefield',
  [LocationType.CAMP]: '⛺ Camp',
  [LocationType.INN]: '🏨 Inn',
  [LocationType.TAVERN]: '🍺 Tavern',
  [LocationType.LANDMARK]: '📍 Landmark',
  
  [LocationType.QUEST_LOCATION]: '❗ Quest Location',
  [LocationType.DANGER_ZONE]: '☠️ Danger Zone',
  
  [LocationType.OTHER]: '📌 Other',
};

export const LocationTypeIcons: Record<LocationType, string> = {
  [LocationType.CITY]: '🏛️',
  [LocationType.TOWN]: '🏘️',
  [LocationType.VILLAGE]: '🏡',
  [LocationType.HAMLET]: '🏠',
  [LocationType.HOMESTEAD]: '🏚️',
  
  [LocationType.CASTLE]: '🏰',
  [LocationType.FORTRESS]: '⛩️',
  [LocationType.RUINS]: '🗿',
  [LocationType.TEMPLE]: '🛕',
  [LocationType.SHRINE]: '⛩️',
  [LocationType.DUNGEON]: '🕳️',
  [LocationType.CAVE]: '🕳️',
  [LocationType.MINE]: '⛏️',
  
  [LocationType.MOUNTAIN_PASS]: '🏔️',
  [LocationType.BRIDGE]: '🌉',
  [LocationType.FORD]: '〰️',
  [LocationType.PORT]: '⚓',
  
  [LocationType.BATTLEFIELD]: '⚔️',
  [LocationType.CAMP]: '⛺',
  [LocationType.INN]: '🏨',
  [LocationType.TAVERN]: '🍺',
  [LocationType.LANDMARK]: '📍',
  
  [LocationType.QUEST_LOCATION]: '❗',
  [LocationType.DANGER_ZONE]: '☠️',
  
  [LocationType.OTHER]: '📌',
};
