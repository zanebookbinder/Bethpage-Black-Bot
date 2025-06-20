import './App.css';
import '@aws-amplify/ui-react/styles.css';
import Homepage from './Homepage.js';

function App() {
  return (
    <div style={{backgroundColor: "white", padding: "3rem", width: "100vw", height: "100vh"}}>
      <Homepage />
    </div>
  )
}

export default App;