import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { makeStyles, tokens, Input, Button, Label, Card, Text, Title3 } from '@fluentui/react-components';
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
  formGroup: {
    marginBottom: tokens.spacingVerticalL,
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalS,
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

function LocalFakeLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  const styles = useStyles();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(username, password);
      navigate('/');
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit}>
        <div className={styles.formGroup}>
          <Label htmlFor="username">Username</Label>
          <Input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter username"
            required
          />
        </div>
        <div className={styles.formGroup}>
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            required
          />
        </div>
        <Button type="submit" appearance="primary" className={styles.submitButton}>
          Login
        </Button>
      </form>
      <Text className={styles.note}>
        Note: This is a stub authentication system. Any username/password will work.
      </Text>
    </>
  );
}

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
  const styles = useStyles();
  const isEntra = config.auth.authMode === 'entra_external_id';

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <Title3 className={styles.title}>Login</Title3>
        <Text className={styles.subtitle}>Welcome to D&amp;D Stats Sheet</Text>
        {isEntra ? <EntraLogin /> : <LocalFakeLogin />}
      </Card>
    </div>
  );
}
