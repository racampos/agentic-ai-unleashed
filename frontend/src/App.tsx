import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LabBrowser } from './features/labs/LabBrowser';
import { LabWorkspace } from './features/labs/LabWorkspace';
import { NIMBanner } from './components/NIMBanner';

function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <NIMBanner />
        <div style={{ flex: 1, minHeight: 0 }}>
          <Routes>
            <Route path="/" element={<LabBrowser />} />
            <Route path="/lab/:labId" element={<LabWorkspace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
