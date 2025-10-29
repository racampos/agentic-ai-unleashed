import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LabBrowser } from './features/labs/LabBrowser';
import { LabWorkspace } from './features/labs/LabWorkspace';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LabBrowser />} />
        <Route path="/lab/:labId" element={<LabWorkspace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
