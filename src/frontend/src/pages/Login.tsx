import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { makeStyles, tokens, Button, Card, Text, Title3 } from '@fluentui/react-components';
import { useMsal } from '@azure/msal-react';
import { useAuth } from '../hooks/useAuth';
import { config } from '../config/service.config';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: tokens.colorNeutralBackground3,
  },
  card: {
    width: '100%',
    maxWidth: '400px',
    padding: tokens.spacingHorizontalXXL,
  },
  title: {
    marginTop: '0',
    marginBottom: tokens.spacingVerticalS,
    textAlign: 'center',
  },
  subtitle: {
    color: tokens.colorNeutralForeground3,
    textAlign: 'center',
    marginTop: '0',
    marginBottom: tokens.spacingVerticalXXL,
  },
  submitButton: {
    width: '100%',
  },
  note: {
    marginTop: tokens.spacingVerticalL,
    padding: tokens.spacingHorizontalL,
    backgroundColor: tokens.colorNeutralBackground1,
    borderLeftWidth: '3px',
    borderLeftStyle: 'solid',
    borderLeftColor: tokens.colorBrandForeground1,
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase300,
    borderRadius: tokens.borderRadiusMedium,
  },
});

function EntraLogin() {
  const { instance, inProgress } = useMsal();
  const [error, setError] = useState<string | null>(null);
  const styles = useStyles();
  const isLoggingIn = inProgress !== 'none';

  const handleMsalLogin = async () => {
    try {
      setError(null);
      await instance.loginRedirect({
        scopes: [config.auth.apiScope],
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
    }
  };

  return (
    <>
      <Button
        appearance="primary"
        className={styles.submitButton}
        onClick={handleMsalLogin}
        disabled={isLoggingIn}
      >
        Sign in with Microsoft
      </Button>
      {error && <Text className={styles.note}>{error}</Text>}
    </>
  );
}

export default function Login() {
  const navigate = useNavigate();
  const styles = useStyles();

  const user = useAuth().user;
  useEffect(() => {
    if (user !== null){
      navigate('/');
    }
  }, [user]);

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <Title3 className={styles.title}>Login</Title3>
        <Text className={styles.subtitle}>Welcome to D&amp;D Stats Sheet</Text>
        <EntraLogin />
      </Card>
    </div>
  );
}
