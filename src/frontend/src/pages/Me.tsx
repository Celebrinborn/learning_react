import { useEffect, useState } from 'react';
import {
  makeStyles,
  tokens,
  Title1,
  Text,
  Spinner,
  MessageBar,
  MessageBarBody,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from '@fluentui/react-components';
import { apiClient } from '../services/apiClient';
import CopyableCode from '../components/common/CopyableCode';

interface PrincipalResponse {
  subject: string;
  issuer: string;
  audience: string;
  expiration: number;
  issued_at: number;
  not_before: number;
  name: string | null;
  prefered_username: string | null;
  entra_object_id: string | null;
}

const useStyles = makeStyles({
  container: {
    padding: tokens.spacingHorizontalXXL,
    maxWidth: '900px',
  },
  header: {
    marginBottom: tokens.spacingVerticalL,
  },
  subtitle: {
    color: tokens.colorNeutralForeground3,
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    padding: tokens.spacingVerticalXXL,
  },
  labelCell: {
    fontWeight: tokens.fontWeightSemibold,
    whiteSpace: 'nowrap',
    verticalAlign: 'top',
    paddingTop: tokens.spacingVerticalM,
  },
  valueCell: {
    verticalAlign: 'top',
    paddingTop: tokens.spacingVerticalM,
  },
});

function formatEpoch(seconds: number): string {
  return new Date(seconds * 1000).toLocaleString();
}

export default function Me() {
  const styles = useStyles();
  const [principal, setPrincipal] = useState<PrincipalResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchMe() {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.fetch('/me');
        if (!response.ok) {
          throw new Error(`Failed to fetch /me: ${response.status} ${response.statusText}`);
        }
        const data: PrincipalResponse = await response.json();
        if (!cancelled) {
          setPrincipal(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load user info');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchMe();
    return () => {
      cancelled = true;
    };
  }, []);

  const rows: { label: string; value: string }[] = principal
    ? [
        { label: 'Subject (sub)', value: principal.subject },
        { label: 'Issuer (iss)', value: principal.issuer },
        { label: 'Audience (aud)', value: principal.audience },
        { label: 'Name', value: principal.name ?? '—' },
        { label: 'Preferred Username', value: principal.prefered_username ?? '—' },
        { label: 'Entra Object ID (oid)', value: principal.entra_object_id ?? '—' },
        { label: 'Issued At (iat)', value: `${principal.issued_at} (${formatEpoch(principal.issued_at)})` },
        { label: 'Not Before (nbf)', value: `${principal.not_before} (${formatEpoch(principal.not_before)})` },
        { label: 'Expiration (exp)', value: `${principal.expiration} (${formatEpoch(principal.expiration)})` },
      ]
    : [];

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Title1>My Account</Title1>
        <Text className={styles.subtitle}>Claims from your authenticated token, via GET /me.</Text>
      </div>

      {loading ? (
        <div className={styles.loading}>
          <Spinner label="Loading..." />
        </div>
      ) : error ? (
        <MessageBar intent="error">
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      ) : (
        <Table aria-label="Authenticated user claims">
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.label}>
                <TableCell className={styles.labelCell}>{row.label}</TableCell>
                <TableCell className={styles.valueCell}>
                  <CopyableCode value={row.value} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
