/**
 * Example Character Sheet - Druid Level 4
 * # Kelthar

**Race:** Silver Dragonborn  
**Class & Level:** Druid 4 (Circle of the Moon)  
**Background:** Far Traveler  
**Alignment:** —  
**Experience Points:** —

---

## Ability Scores

| Ability | Score | Modifier |
|--------|------:|--------:|
| Strength | 9 | −1 |
| Dexterity | 13 | +1 |
| Constitution | 14 | +2 |
| Intelligence | 10 | +0 |
| Wisdom | 16 | +3 |
| Charisma | 15 | +2 |

**Proficiency Bonus:** +2  
**Passive Wisdom (Perception):** 15

---

## Combat Statistics

- **Armor Class:** 12  
- **Initiative:** +1  
- **Speed:** 30 ft  
- **Hit Point Maximum:** 31  
- **Current Hit Points:** 31  
- **Temporary Hit Points:** —

---

## Saving Throws

- Strength
- Dexterity
- Constitution
- Intelligence
- **Wisdom (Proficient)**
- Charisma

---

## Skills

**Proficient**
- Nature (Int)
- Perception (Wis)

**Other Skills**
- Acrobatics (Dex)
- Animal Handling (Wis)
- Arcana (Int)
- Athletics (Str)
- Deception (Cha)
- History (Int)
- Insight (Wis)
- Intimidation (Cha)
- Investigation (Int)
- Medicine (Wis)
- Performance (Cha)
- Persuasion (Cha)
- Religion (Int)
- Sleight of Hand (Dex)
- Stealth (Dex)
- Survival (Wis)

---

## Attacks & Weapons

| Weapon | Damage | Notes |
|------|--------|------|
| Quarterstaff | 1d6 bludgeoning | Versatile (1d8) |
| Shortbow | 1d6 piercing | Ammunition |

---

## Class & Racial Features

### Circle of the Moon
- Combat Wild Shape
- Circle Forms

### Dragonborn Breath Weapon (Cold)
- **Area:** 15-ft cone  
- **Save:** Constitution  
- **DC:** 12  
- **Damage:** 2d6 cold  
- **Effect:** Half damage on successful save

---

## Feat

### Ritual Caster (Wizard)

**Ritual Spellbook**
- *Find Familiar*
- *Unseen Servant*

---

## Equipment

- Ritual spellbook
- Leather armor
- Explorer’s pack
- Yew staff
- 10 gp medallion

---

## Languages & Proficiencies

- Common
- Draconic
- Druidic
- Dragon Chess

---

## Roleplay

### Personality Traits
—

### Ideals
—

### Bonds
—

### Flaws
—

 */



import { makeStyles, tokens, Badge } from "@fluentui/react-components";
import { useState, useEffect } from "react";
import Box, { BoxWidth } from "../components/character_sheet/Box";

const useStyles = makeStyles({
  container: {
    columnWidth: `${BoxWidth.tripleBox}px`,  // Use predefined width from dimentions.ts
    columnGap: tokens.spacingHorizontalL,
    padding: tokens.spacingHorizontalL,
  },

  widthIndicator: {
    position: "fixed",
    bottom: tokens.spacingVerticalM,
    right: tokens.spacingHorizontalM,
    zIndex: 1000,
  },
});

export default function CharacterCreator() {
  const styles = useStyles();
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className={styles.container}>
      <Badge
        className={styles.widthIndicator}
        appearance="filled"
        color="informative"
        size="large"
      >
        {windowWidth}px
      </Badge>

      {/* Ability Scores */}
      <Box gridRowSpan={2} title="Ability Scores">
        <p><strong>Strength:</strong> 9 (−1)</p>
        <p><strong>Dexterity:</strong> 13 (+1)</p>
        <p><strong>Constitution:</strong> 14 (+2)</p>
        <p><strong>Intelligence:</strong> 10 (+0)</p>
        <p><strong>Wisdom:</strong> 16 (+3)</p>
        <p><strong>Charisma:</strong> 15 (+2)</p>
      </Box>

      {/* Combat Statistics */}
      <Box gridRowSpan={2} title="Combat Statistics">
        <p><strong>Armor Class:</strong> 12</p>
        <p><strong>Initiative:</strong> +1</p>
        <p><strong>Speed:</strong> 30 ft</p>
        <p><strong>Hit Point Max:</strong> 31</p>
        <p><strong>Current HP:</strong> 31</p>
        <p><strong>Temporary HP:</strong> —</p>
      </Box>

      {/* Saving Throws */}
      <Box gridRowSpan={2} title="Saving Throws">
        <p>Strength</p>
        <p>Dexterity</p>
        <p>Constitution</p>
        <p>Intelligence</p>
        <p><strong>Wisdom (Proficient)</strong></p>
        <p>Charisma</p>
      </Box>

      {/* Skills */}
      <Box gridRowSpan={4} title="Skills">
        <p>Acrobatics (Dex)</p>
        <p>Animal Handling (Wis)</p>
        <p>Arcana (Int)</p>
        <p>Athletics (Str)</p>
        <p>Deception (Cha)</p>
        <p>History (Int)</p>
        <p>Insight (Wis)</p>
        <p>Intimidation (Cha)</p>
        <p>Investigation (Int)</p>
        <p>Medicine (Wis)</p>
        <p><strong>Nature (Int) - Proficient</strong></p>
        <p><strong>Perception (Wis) - Proficient</strong></p>
        <p>Performance (Cha)</p>
        <p>Persuasion (Cha)</p>
        <p>Religion (Int)</p>
        <p>Sleight of Hand (Dex)</p>
        <p>Stealth (Dex)</p>
        <p>Survival (Wis)</p>
      </Box>

      {/* Attacks & Weapons */}
      <Box gridRowSpan={2} title="Attacks & Weapons">
        <p><strong>Quarterstaff:</strong> 1d6 bludgeoning (Versatile 1d8)</p>
        <p><strong>Shortbow:</strong> 1d6 piercing (Ammunition)</p>
      </Box>

      {/* Equipment */}
      <Box gridRowSpan={2} title="Equipment">
        <p>Ritual spellbook</p>
        <p>Leather armor</p>
        <p>Explorer's pack</p>
        <p>Yew staff</p>
        <p>10 gp medallion</p>
      </Box>

      {/* Class & Racial Features */}
      <Box gridRowSpan={3} title="Class & Racial Features">
        <p><strong>Circle of the Moon</strong></p>
        <p>- Combat Wild Shape</p>
        <p>- Circle Forms</p>
        <p><strong>Dragonborn Breath (Cold):</strong></p>
        <p>15-ft cone, DC 12 Con save, 2d6 cold damage</p>
      </Box>

      {/* Feat */}
      <Box gridRowSpan={2} title="Feat: Ritual Caster (Wizard)">
        <p><strong>Ritual Spellbook:</strong></p>
        <p>- Find Familiar</p>
        <p>- Unseen Servant</p>
      </Box>

      {/* Languages & Proficiencies */}
      <Box gridRowSpan={2} title="Languages & Proficiencies">
        <p>Common</p>
        <p>Draconic</p>
        <p>Druidic</p>
        <p>Dragon Chess</p>
      </Box>

      {/* Personality */}
      <Box gridRowSpan={3} title="Personality Traits">
        <p>Personality traits go here</p>
      </Box>

      {/* Ideals */}
      <Box gridRowSpan={2} title="Ideals">
        <p>Ideals go here</p>
      </Box>

      {/* Bonds */}
      <Box gridRowSpan={2} title="Bonds">
        <p>Bonds go here</p>
      </Box>

      {/* Flaws */}
      <Box gridRowSpan={2} title="Flaws">
        <p>Flaws go here</p>
      </Box>
    </div>
  );
}
