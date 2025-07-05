import { Routes, Route } from 'react-router-dom';
import Homepage from './Homepage';
import OneTimeLinkValidator from './components/OneTimeLinkValidator';
import TabWrapper from './TabWrapper';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Homepage />} />
      <Route path="/updateSettings/:guid" element={<TabWrapper component={<OneTimeLinkValidator />} />} />
    </Routes>
  );
}
