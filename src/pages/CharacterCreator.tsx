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
    display: "flex",
    flexWrap: "wrap",
    gap: tokens.spacingHorizontalL,
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

      {/* Example boxes - replace with real content */}
      <Box basis={BoxWidth.smallBox} title="Ability Scores">
        <p>
          <strong>Strength:</strong> 16 (+3)
        </p>
        <p>
          <strong>Dexterity:</strong> 12 (+1)
        </p>
        <p>
          <strong>Constitution:</strong> 14 (+2)
        </p>
        <p>
          <strong>Intelligence:</strong> 10 (+0)
        </p>
        <p>
          <strong>Wisdom:</strong> 11 (+0)
        </p>
        <p>
          <strong>Charisma:</strong> 10 (+0)
        </p>
      </Box>

      <Box basis={BoxWidth.doubleBox} grow={2} title="Skills">
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
        <p>Nature (Int)</p>
        <p>Perception (Wis)</p>
        <p>Performance (Cha)</p>
        <p>Persuasion (Cha)</p>
        <p>Religion (Int)</p>
        <p>Sleight of Hand (Dex)</p>
        <p>Stealth (Dex)</p>
        <p>Survival (Wis)</p>
      </Box>

      <Box basis={BoxWidth.tripleBox} grow={3}>
        <h2>Equipment</h2>
        <p>Equipment goes here</p>
      </Box>
    </div>
  );
}
