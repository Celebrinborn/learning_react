import { Link } from 'react-router-dom';
import dragonImage from '../assets/404_dragon.png';

export default function NotFound() {
  return (
    <div style={{ 
      textAlign: 'center', 
      padding: '4rem 2rem',
      minHeight: '60vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <img 
        src={dragonImage} 
        alt="Sad dragon holding 404 sign" 
        style={{ width: '400px', maxWidth: '90%', height: 'auto', marginBottom: '1rem' }}
      />
      <h1 style={{ fontSize: '6rem', margin: '0', color: '#646cff' }}>404</h1>
      <h2 style={{ fontSize: '2rem', margin: '1rem 0' }}>Page Not Found</h2>
      <p style={{ fontSize: '1.2rem', color: '#888', marginBottom: '2rem' }}>
        The page you're looking for doesn't exist.
      </p>
      <Link 
        to="/" 
        style={{
          padding: '0.75rem 1.5rem',
          background: '#646cff',
          color: '#fff',
          textDecoration: 'none',
          borderRadius: '8px',
          fontWeight: '500',
          transition: 'background 0.2s'
        }}
      >
        Go Home
      </Link>
    </div>
  );
}
