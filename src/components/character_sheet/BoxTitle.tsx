import { makeStyles, tokens } from "@fluentui/react-components";
import type { ReactNode } from "react";

export { BoxWidth } from "./dimentions";

export interface BoxProps {
  title?: string;
}

const useStyles = makeStyles({
    container: {
        
    },
    title: {
        fontSize: tokens.fontSizeBase100,
        fontStyle: "italic",
        textAlign: "center",
    }
});

export default function BoxTitle({ title = "" }: BoxProps) {
    const styles = useStyles();
    if (title.length === 0) return null;
    return (
        <div className = {styles.container}>
            <svg viewBox="0 0 100 1">
                <line x1="5" x2="95" y1="0" y2="1" stroke={tokens.colorNeutralForeground1} strokeWidth=".5"/>
            </svg>
            <div className={styles.title}>{title}</div>
        </div>
    )
}