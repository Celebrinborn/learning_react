/**
 * ErrorDisplay Component - Error message display with copy-to-clipboard
 * Displays error messages with copy-to-clipboard functionality
 */

import { MessageBar, MessageBarBody, MessageBarActions, Button } from '@fluentui/react-components';
import { Dismiss24Regular, Copy24Regular } from '@fluentui/react-icons';

interface ErrorDisplayProps {
  isOpen: boolean;
  errorMessage: string;
  onDismiss: () => void;
}

export default function ErrorDisplay({ isOpen, errorMessage, onDismiss }: ErrorDisplayProps) {
  if (!isOpen) return null;

  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(errorMessage);
    } catch (err) {
      console.error('Failed to copy error message:', err);
    }
  };

  return (
    <MessageBar intent="error">
      <MessageBarBody>{errorMessage}</MessageBarBody>
      <MessageBarActions>
        <Button
          appearance="transparent"
          icon={<Copy24Regular />}
          onClick={handleCopyToClipboard}
          aria-label="Copy error to clipboard"
        />
        <Button
          appearance="transparent"
          icon={<Dismiss24Regular />}
          onClick={onDismiss}
          aria-label="Dismiss error"
        />
      </MessageBarActions>
    </MessageBar>
  );
}
