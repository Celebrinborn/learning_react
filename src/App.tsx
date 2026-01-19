import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { FluentProvider, webDarkTheme } from '@fluentui/react-components';
import MainLayout from './components/layout/MainLayout';
import Home from './pages/Home';
import CharacterCreator from './pages/CharacterCreator';
import Campaign from './pages/Campaign';
import Settings from './pages/Settings';
import Login from './pages/Login';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <FluentProvider theme={webDarkTheme}>
      <BrowserRouter>
        <Routes>
          {/* Routes with layout (includes TopNav) */}
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Home />} />
            <Route path="character_creator" element={<CharacterCreator />} />
            <Route path="campaign" element={<Campaign />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Route>

          {/* Routes without layout */}
          <Route path="/login" element={<Login />} />
        </Routes>
      </BrowserRouter>
    </FluentProvider>
  );
}
