import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './components/AuthProvider'
import HomePage from './pages/HomePage'
import CreatePage from './pages/CreatePage'
import ManagePage from './pages/ManagePage'
import AccessPage from './pages/AccessPage'
import ApiAccess from './pages/ApiAccess.tsx'

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/create" element={<CreatePage />} />
          <Route path="/manage" element={<ManagePage />} />
          <Route path="/access/:name" element={<AccessPage />} />
          <Route path="/object/:token" element={<AccessPage />} />
          <Route path="/api/:name" element={<ApiAccess />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App