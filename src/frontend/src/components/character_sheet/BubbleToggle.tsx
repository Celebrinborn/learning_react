/**
 * BubbleToggle Component
 *
 * A circular toggle indicator that displays as either filled or empty.
 * Used for proficiency markers, death saves, and other binary state indicators
 * on D&D character sheets.
 *
 * @param isSelected - Boolean to control filled (true) or empty (false) state
 * @param onClick - Optional callback function when the circle is clicked
 */

import { makeStyles, tokens } from "@fluentui/react-components";

export interface BubbleToggleProps {
  isSelected: boolean;
  onClick?: () => void;
}

const useStyles = makeStyles({
  bubble: {
    width: "16px",
    height: "16px",
    borderRadius: "50%",
    border: `2px solid ${tokens.colorNeutralStroke1}`,
    cursor: "pointer",
  },
  selected: {
    backgroundColor: tokens.colorNeutralForeground1,
  },
});

// TODO: Implement component
export default function BubbleToggle({ isSelected, onClick }: BubbleToggleProps) {
  const styles = useStyles();
  return (
    <div
      className={`${styles.bubble} ${isSelected ? styles.selected : ""}`}
      onClick={onClick}
    />
  );
}
