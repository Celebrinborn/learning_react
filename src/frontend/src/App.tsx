import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { FluentProvider, webDarkTheme } from '@fluentui/react-components';
import { useEffect } from 'react';
import { getTracer } from './telemetry';
import MainLayout from './components/layout/MainLayout';
import ProtectedRoute from './components/layout/ProtectedRoute';
import Home from './pages/Home';
import CharacterCreator from './pages/CharacterCreator';
import Campaign from './pages/Campaign';
import Settings from './pages/Settings';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import EncounterBuilder from './pages/EncounterBuilder';
import EncounterPlayer from './pages/EncounterPlayer';
import Map from './pages/Map';
import Homebrew from './pages/Homebrew';

/**
 * Component to track route changes with OpenTelemetry
 */
function RouteTracker() {
  const location = useLocation();

  useEffect(() => {
    const tracer = getTracer();
    const span = tracer.startSpan('route_navigation');
    span.setAttribute('route.path', location.pathname);
    span.setAttribute('route.search', location.search);
    span.end();
  }, [location]);

  return null;
}

export default function App() {
  return (
    <FluentProvider theme={webDarkTheme}>
      <BrowserRouter>
        <RouteTracker />
        <Routes>
          {/* Routes with layout (includes TopNav) */}
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Home />} />
            <Route path="character_creator" element={<ProtectedRoute allowedRoles={['player', 'dm']}><CharacterCreator /></ProtectedRoute>} />
            <Route path="campaign" element={<Campaign />} />
            <Route path="settings" element={<ProtectedRoute allowedRoles={['dm']}><Settings /></ProtectedRoute>} />
            <Route path="encounter_builder" element={<ProtectedRoute allowedRoles={['dm']}><EncounterBuilder /></ProtectedRoute>} />
            <Route path="encounter_player" element={<ProtectedRoute allowedRoles={['dm']}><EncounterPlayer /></ProtectedRoute>} />
            <Route path="map" element={<ProtectedRoute allowedRoles={['dm']}><Map /></ProtectedRoute>} />
            <Route path="homebrew/*" element={<Homebrew />} />
            <Route path="*" element={<NotFound />} />
          </Route>

          {/* Routes without layout */}
          <Route path="/login" element={<Login />} />
        </Routes>
      </BrowserRouter>
    </FluentProvider>
  );
}
