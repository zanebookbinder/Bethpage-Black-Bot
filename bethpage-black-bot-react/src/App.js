import { Routes, Route } from 'react-router-dom';
import Homepage from './Homepage';
import OneTimeLinkValidator from './components/OneTimeLinkValidator';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Homepage />} />
      <Route path="/updateSettings/:guid" element={<OneTimeLinkValidator />} />
    </Routes>
  );
}
