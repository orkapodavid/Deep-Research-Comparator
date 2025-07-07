import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Leaderboard } from './components/Leaderboard';
import { DeepResearchPage } from './components/Page';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-[#F9F7F7]">
        <nav className="bg-[#213555] shadow-sm">
          <div className="max-w-6xl mx-auto px-0 py-3">
            <div className="flex justify-between items-center px-4">
              <Link to="/" className="text-xl font-bold text-[#F5EFE7]">
                Deep Research Comparator
              </Link>
              <div className="space-x-4">
                <Link to="/" className="text-[#F5EFE7] hover:text-white transition-colors">
                  Home
                </Link>
                <Link to="/leaderboard" className="text-[#F5EFE7] hover:text-white transition-colors">
                  Ranking
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<DeepResearchPage />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;