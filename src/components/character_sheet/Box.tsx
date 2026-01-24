import { makeStyles, tokens } from "@fluentui/react-components";
import type { ReactNode } from "react";
import BoxTitle from "./BoxTitle";

export { BoxWidth } from "./dimentions";

export interface BoxProps {
  children: ReactNode;
  /** flex-basis in px (default: 300) */
  basis?: number;
  /** flex-grow for large displays (default: 1) */
  grow?: number;
  /** flex-shrink (default: 1) */
  shrink?: number;
  /**title (default blank) */
  title?: string;
}

const useStyles = makeStyles({
  box: {
    backgroundColor: tokens.colorNeutralBackground1,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
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

export default function Box({
  children,
  basis = 300,
  grow = 1,
  shrink = 1,
  title = "",
}: BoxProps) {
  return (
    <div
      className={useStyles().box}
      style={{
        flex: `${grow} ${shrink} ${basis}px`,
      }}
    >
      {children}
      <BoxTitle title={title} />
    </div>
  );
}
