import { Outlet } from 'react-router-dom';
import { makeStyles, tokens } from '@fluentui/react-components';
import TopNav from './TopNav';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
  },
  main: {
    flex: '1',
    padding: tokens.spacingHorizontalXXL,
  },
});

export default function MainLayout() {
  const styles = useStyles();

  return (
    <div className={styles.container}>
      <TopNav />
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
