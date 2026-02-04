import { NavLink } from 'react-router-dom';
import { makeStyles, tokens, Button, Menu, MenuTrigger, MenuPopover, MenuList, MenuItem } from '@fluentui/react-components';
import { useAuth } from '../../hooks/useAuth';
import { navigationLinks } from '../../config/navigation';
import logoDragon from '../../assets/Logo_dragon.png';
import HomebrewMenu from './HomebrewMenu';

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
  logo: {
    height: '32px',  // Small height
    width: 'auto',
    display: 'block',
  },
  menuTrigger: {
    color: tokens.colorNeutralForeground3,
    textDecoration: 'none',
    fontWeight: tokens.fontWeightSemibold,
    cursor: 'pointer',
    ':hover': {
      color: tokens.colorNeutralForeground1,
    },
  },
  menuItem: {
    textDecoration: 'none',
    color: 'inherit',
    display: 'block',
    width: '100%',
  },
});

export default function TopNav() {
  const { user, logout } = useAuth();
  const styles = useStyles();

  return (
    <header className={styles.header}>
      <nav className={styles.nav}>
        <div className={styles.navLinks}>
          <NavLink to="/">
            <img src={logoDragon} alt="Logo" className={styles.logo} />
          </NavLink>
          {navigationLinks.map((link) => {
            // Dynamic homebrew dropdown
            if (link.path === '/homebrew') {
              return <HomebrewMenu key={link.path} triggerClassName={styles.menuTrigger} />;
            }

            return link.children ? (
              // Dropdown menu
              <Menu key={link.path}>
                <MenuTrigger disableButtonEnhancement>
                  <span className={styles.menuTrigger}>{link.label}</span>
                </MenuTrigger>
                <MenuPopover>
                  <MenuList>
                    {link.children.map((child) => (
                      <MenuItem key={child.path}>
                        <NavLink to={child.path} className={styles.menuItem}>
                          {child.label}
                        </NavLink>
                      </MenuItem>
                    ))}
                  </MenuList>
                </MenuPopover>
              </Menu>
            ) : (
              // Regular link
              <NavLink
                key={link.path}
                to={link.path}
                className={({ isActive }) =>
                  isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
                }
              >
                {link.label}
              </NavLink>
            );
          })}
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
