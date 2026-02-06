import { makeStyles, tokens } from "@fluentui/react-components";

export interface BoxProps {
  /** The name of the stat (e.g., "Strength", "Dexterity") */
  statName: string;
  /** The base value of the stat (e.g., 16, 12). The modifier is calculated as */
  statBaseValue: number;
  /** flex-basis in px (default: 100) */
  basis?: number;
}

const useStyles = makeStyles({
  statsBox: {
    backgroundColor: tokens.colorNeutralBackground2,
    border: `4px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: "4px",
    boxShadow: tokens.shadow2,
    padding: tokens.spacingHorizontalL,

    // Print styles
    "@media print": {
      boxShadow: "none",
      breakInside: "avoid",
    },
  },
});

export default function StatsBox({ statName, statBaseValue, basis = 100 }: BoxProps) {
  return (
    <div
      className={useStyles().statsBox}
      style={{
        flex: `1 1 ${basis}px`,
      }}
    >
      <h2>{statName}</h2>
      <p>{statBaseValue}</p>
    </div>
  );
}
