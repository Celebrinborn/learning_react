import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { makeStyles, tokens, Input, Button, Label, Card, Text, Title3 } from '@fluentui/react-components';
import { useAuth } from '../hooks/useAuth';

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

export default function Login() {
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
    <div className={styles.container}>
      <Card className={styles.card}>
        <Title3 className={styles.title}>Login</Title3>
        <Text className={styles.subtitle}>Welcome to D&D Stats Sheet</Text>
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
      </Card>
    </div>
  );
}
