import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container } from '@mui/material';
import NavBar from './components/NavBar';
import PaperEvaluation from './pages/PaperEvaluation';
import KnowledgeBase from './pages/KnowledgeBase';
import PaperLibrary from './pages/PaperLibrary';
import ModelManagement from './pages/ModelManagement';

// 创建主题
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <NavBar />
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Routes>
            <Route path="/" element={<PaperEvaluation />} />
            <Route path="/knowledge" element={<KnowledgeBase />} />
            <Route path="/library" element={<PaperLibrary />} />
            <Route path="/model" element={<ModelManagement />} />
          </Routes>
        </Container>
      </Router>
    </ThemeProvider>
  );
}

export default App;
