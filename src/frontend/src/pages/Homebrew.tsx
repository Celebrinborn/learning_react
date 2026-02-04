import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  makeStyles,
  tokens,
  Title1,
  Spinner,
  MessageBar,
  MessageBarBody,
} from '@fluentui/react-components';
import ReactMarkdown from 'react-markdown';
import { homebrewService } from '../services/homebrewService';
import type { HomebrewDocument } from '../types/homebrew';

const useStyles = makeStyles({
  container: {
    padding: tokens.spacingHorizontalXXL,
    maxWidth: '900px',
  },
  header: {
    marginBottom: tokens.spacingVerticalL,
  },
  content: {
    '& h1': {
      fontSize: tokens.fontSizeHero800,
      marginTop: tokens.spacingVerticalXXL,
      marginBottom: tokens.spacingVerticalM,
    },
    '& h2': {
      fontSize: tokens.fontSizeHero700,
      marginTop: tokens.spacingVerticalXL,
      marginBottom: tokens.spacingVerticalM,
    },
    '& h3': {
      fontSize: tokens.fontSizeBase600,
      marginTop: tokens.spacingVerticalL,
      marginBottom: tokens.spacingVerticalS,
    },
    '& p': {
      marginBottom: tokens.spacingVerticalM,
      lineHeight: tokens.lineHeightBase400,
    },
    '& ul, & ol': {
      paddingLeft: tokens.spacingHorizontalXXL,
      marginBottom: tokens.spacingVerticalM,
    },
    '& li': {
      marginBottom: tokens.spacingVerticalXS,
    },
    '& code': {
      backgroundColor: tokens.colorNeutralBackground3,
      padding: `${tokens.spacingVerticalXXS} ${tokens.spacingHorizontalXS}`,
      borderRadius: tokens.borderRadiusSmall,
      fontFamily: 'monospace',
    },
    '& pre': {
      backgroundColor: tokens.colorNeutralBackground3,
      padding: tokens.spacingHorizontalM,
      borderRadius: tokens.borderRadiusMedium,
      overflow: 'auto',
    },
    '& blockquote': {
      borderLeft: `4px solid ${tokens.colorBrandStroke1}`,
      paddingLeft: tokens.spacingHorizontalL,
      marginLeft: '0',
      fontStyle: 'italic',
    },
    '& table': {
      borderCollapse: 'collapse',
      width: '100%',
      marginBottom: tokens.spacingVerticalM,
    },
    '& th, & td': {
      border: `1px solid ${tokens.colorNeutralStroke1}`,
      padding: tokens.spacingHorizontalS,
      textAlign: 'left',
    },
    '& th': {
      backgroundColor: tokens.colorNeutralBackground3,
    },
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    padding: tokens.spacingVerticalXXL,
  },
});

export default function Homebrew() {
  const styles = useStyles();
  const params = useParams();
  const docPath = params['*'];

  const [document, setDocument] = useState<HomebrewDocument | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!docPath) {
      setDocument(null);
      return;
    }

    async function fetchDocument() {
      setLoading(true);
      setError(null);
      try {
        const doc = await homebrewService.getById(docPath!);
        setDocument(doc);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load document');
      } finally {
        setLoading(false);
      }
    }
    fetchDocument();
  }, [docPath]);

  return (
    <div className={styles.container}>
      {loading ? (
        <div className={styles.loading}>
          <Spinner label="Loading..." />
        </div>
      ) : error ? (
        <MessageBar intent="error">
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      ) : document ? (
        <div className={styles.content}>
          <ReactMarkdown>{document.content}</ReactMarkdown>
        </div>
      ) : (
        <div className={styles.header}>
          <Title1>Homebrew Content</Title1>
          <p>Select a document from the Homebrew menu above.</p>
        </div>
      )}
    </div>
  );
}
