import { NavLink } from 'react-router-dom';
import { makeStyles, tokens, Button } from '@fluentui/react-components';
import { useAuth } from '../../hooks/useAuth';
import { navigationLinks } from '../../config/navigation';

const useStyles = makeStyles({
  header: {
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    borderBottomColor: tokens.colorNeutralStroke2,
    position: 'sticky',
    top: '0',
    zIndex: '100',
  },
  nav: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    maxWidth: '1200px',
    margin: '0 auto',
    paddingTop: tokens.spacingVerticalL,
    paddingBottom: tokens.spacingVerticalL,
    paddingLeft: tokens.spacingHorizontalXXL,
    paddingRight: tokens.spacingHorizontalXXL,
  },
  navLinks: {
    display: 'flex',
    gap: tokens.spacingHorizontalXXL,
  },
  navLink: {
    color: tokens.colorNeutralForeground3,
    textDecoration: 'none',
    fontWeight: tokens.fontWeightSemibold,
    transitionProperty: 'color',
    transitionDuration: '0.2s',
    ':hover': {
      color: tokens.colorNeutralForeground1,
    },
  },
  navLinkActive: {
    color: tokens.colorBrandForeground1,
  },
  authControls: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalL,
  },
  userName: {
    color: tokens.colorNeutralForeground1,
    fontSize: tokens.fontSizeBase300,
  },
  loginLink: {
    color: tokens.colorBrandForeground1,
    textDecoration: 'none',
    fontWeight: tokens.fontWeightSemibold,
  },
});

export default function TopNav() {
  const { user, logout } = useAuth();
  const styles = useStyles();

  return (
    <header className={styles.header}>
      <nav className={styles.nav}>
        <div className={styles.navLinks}>
          {navigationLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) => 
                isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
        
        <div className={styles.authControls}>
          {user ? (
            <>
              <span className={styles.userName}>{user.name}</span>
              <Button appearance="outline" onClick={logout}>
                Logout
              </Button>
            </>
          ) : (
            <NavLink to="/login" className={styles.loginLink}>
              <Button appearance="outline">Login</Button>
            </NavLink>
          )}
        </div>
      </nav>
    </header>
  );
}
