/**
 * CopyableCode - renders a value in a monospace box with a copy-to-clipboard button.
 */
import { useState } from 'react';
import { makeStyles, tokens, Button, Tooltip } from '@fluentui/react-components';
import { Copy16Regular, Checkmark16Regular } from '@fluentui/react-icons';

const useStyles = makeStyles({
  root: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalXS,
  },
  code: {
    backgroundColor: tokens.colorNeutralBackground3,
    padding: `${tokens.spacingVerticalXXS} ${tokens.spacingHorizontalS}`,
    borderRadius: tokens.borderRadiusSmall,
    fontFamily: 'monospace',
    fontSize: tokens.fontSizeBase200,
    wordBreak: 'break-all',
  },
});

interface CopyableCodeProps {
  value: string;
}

export default function CopyableCode({ value }: CopyableCodeProps) {
  const styles = useStyles();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  return (
    <div className={styles.root}>
      <code className={styles.code}>{value}</code>
      <Tooltip content={copied ? 'Copied!' : 'Copy'} relationship="label">
        <Button
          appearance="subtle"
          size="small"
          icon={copied ? <Checkmark16Regular /> : <Copy16Regular />}
          onClick={handleCopy}
          aria-label="Copy to clipboard"
        />
      </Tooltip>
    </div>
  );
}
