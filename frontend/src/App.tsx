import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LabBrowser } from './features/labs/LabBrowser';
import { LabWorkspace } from './features/labs/LabWorkspace';
import { NIMBanner } from './components/NIMBanner';

function App() {
  return (
    <BrowserRouter>
      <NIMBanner />
      <Routes>
        <Route path="/" element={<LabBrowser />} />
        <Route path="/lab/:labId" element={<LabWorkspace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
