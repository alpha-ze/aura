import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <HashRouter>
      <App />
      <Toaster
        position="top-center"
        toastOptions={{
          style: {
            background: "rgba(26, 26, 46, 0.95)",
            color: "#fff",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "12px",
            fontSize: "13px",
            backdropFilter: "blur(12px)",
          },
          success: {
            iconTheme: { primary: "#6272f8", secondary: "#fff" },
          },
          error: {
            iconTheme: { primary: "#ef4444", secondary: "#fff" },
          },
        }}
      />
    </HashRouter>
  </React.StrictMode>
);
