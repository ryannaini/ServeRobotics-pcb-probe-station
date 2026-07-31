{/* 1. You open localhost:5173 in the browser
2. Browser loads index.html
3. index.html loads main.jsx
4. Vite transforms your JSX → normal JavaScript
5. Browser runs that JavaScript
6. main.jsx tells React to render <App /> into #root
7. You see your dashboard */}


{/* Vite vs. React 
  1. Vite, transforms .jsx into browser-friendly JavaScript
        - // You write this:
            <p>X: {position.x}</p>
            // Vite turns it into something like:
            React.createElement("p", null, "X: ", position.x)
  2. Takes that JS and updates the webpage when state changes, draws from it  */ }

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx' 

{/* createRoot finds the root mentioned in index.html and opens that container, StrictMode is a react Development helper.
  it wraps your app and turns on extra checks while you're building, catches bugs, warns about outdated or unsafe patterns
  pretty much extra development warnings, the <App /> means run the App function and put whatever it returns on the screen*/};

createRoot(document.getElementById('root')).render(  
  <StrictMode>
    <App />
  </StrictMode>,
)
