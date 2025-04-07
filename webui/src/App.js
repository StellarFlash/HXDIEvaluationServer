import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import EvaluationSpecs from './pages/EvaluationSpecs';
import Evidences from './pages/Evidences';
import Reports from './pages/Reports';
import Database from './pages/Database';
import Navbar from './components/Navbar';

function App() {
  return (
    <div className="app">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/evaluation-specs" element={<EvaluationSpecs />} />
          <Route path="/evidences" element={<Evidences />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/database" element={<Database />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
