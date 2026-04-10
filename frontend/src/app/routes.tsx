import { createBrowserRouter } from 'react-router';
import { Landing } from './pages/Landing';
import { ModeSelect } from './pages/ModeSelect';
import { ScaffoldForm } from './pages/ScaffoldForm';
import { AnalyzeForm } from './pages/AnalyzeForm';
import { Settings } from './pages/Settings';
import { NotFound } from './pages/NotFound';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Landing,
  },
  {
    path: '/generate',
    Component: ModeSelect,
  },
  {
    path: '/generate/scaffold',
    Component: ScaffoldForm,
  },
  {
    path: '/generate/analyze',
    Component: AnalyzeForm,
  },
  {
    path: '/settings',
    Component: Settings,
  },
  {
    path: '*',
    Component: NotFound,
  },
]);