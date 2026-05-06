import Header from './components/Header';
import MainContent from './components/MainContent';
import Footer from './components/Footer';
import './App.css';

function App() {
  return (
    <div className="container">
      {/* 쪼개놓은 부품(컴포넌트)들을 조립합니다 */}
      <Header />
      <MainContent />
      <Footer />
    </div>
  );
}

export default App;