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
  /** Number of grid rows to span (default: 1) */
  gridRowSpan?: number;
}

const useStyles = makeStyles({
  box: {
    backgroundColor: tokens.colorNeutralBackground1,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: "4px",
    boxShadow: tokens.shadow2,
    padding: tokens.spacingHorizontalL,
    alignSelf: "start",
    breakInside: "avoid",  // Prevent boxes from splitting across columns
    marginBottom: tokens.spacingVerticalL,  // Vertical spacing between boxes
    // display: "flex",
    // flexDirection: "column",
    // // justifyContent: "space-between",
    // height: "100%",
    // // overflow: ""

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
  gridRowSpan: _gridRowSpan = 1,
}: BoxProps) {
  return (
    <div
      className={useStyles().box}
      style={{
        flex: `${grow} ${shrink} ${basis}px`,
        // gridRow: `span ${gridRowSpan}`,
      }}
    >
      {children}
      <BoxTitle title={title} />
    </div>
  );
}
