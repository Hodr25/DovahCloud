// Componente encargado de gestionar el flujo de inicio de sesión.
import { useState } from "react";
import { motion } from "framer-motion";

export function LoginForm({ onSubmit, loading, error }) {
  // Estado local para capturar el usuario.
  const [username, setUsername] = useState("");
  // Estado local para capturar la contraseña.
  const [password, setPassword] = useState("");

  // Enviamos las credenciales al padre para que gestione la autenticación.
  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({ username, password });
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      className="glass-panel"
      style={{
        position: "relative",
        padding: "2.8rem",
        display: "flex",
        flexDirection: "column",
        gap: "1.5rem",
        width: "min(420px, 90vw)",
        boxShadow: "var(--shadow-strong)",
      }}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <div>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "0.5rem" }}>DovahCloud</h1>
        <p style={{ color: "var(--color-text-secondary)", lineHeight: 1.5 }}>
          Accede a tu nube multimedia privada con una experiencia moderna y envolvente.
        </p>
      </div>

      <label style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        <span style={{ fontWeight: 600, letterSpacing: "0.02em" }}>Usuario</span>
        <input
          type="text"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          placeholder="Nombre de usuario"
          required
          style={{
            padding: "0.9rem 1.1rem",
            borderRadius: "var(--radius-sm)",
            border: "1px solid rgba(163, 123, 255, 0.28)",
            background: "rgba(11, 5, 22, 0.7)",
            color: "var(--color-text-primary)",
            outline: "none",
          }}
        />
      </label>

      <label style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        <span style={{ fontWeight: 600, letterSpacing: "0.02em" }}>Contraseña</span>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="••••••••"
          required
          style={{
            padding: "0.9rem 1.1rem",
            borderRadius: "var(--radius-sm)",
            border: "1px solid rgba(163, 123, 255, 0.28)",
            background: "rgba(11, 5, 22, 0.7)",
            color: "var(--color-text-primary)",
            outline: "none",
          }}
        />
      </label>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            background: "rgba(255, 94, 94, 0.14)",
            border: "1px solid rgba(255, 94, 94, 0.35)",
            padding: "0.9rem 1.1rem",
            borderRadius: "var(--radius-sm)",
            color: "#ffaeae",
            fontWeight: 500,
          }}
        >
          {error}
        </motion.div>
      )}

      <motion.button
        type="submit"
        className="primary-button"
        whileTap={{ scale: 0.98 }}
        disabled={loading}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0.6rem",
          opacity: loading ? 0.65 : 1,
          cursor: loading ? "progress" : "pointer",
        }}
      >
        {loading ? "Verificando..." : "Entrar en la plataforma"}
      </motion.button>

      <p style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)", textAlign: "center" }}>
        Consejo: activa el acceso privado desde el panel si tu cuenta lo permite.
      </p>
    </motion.form>
  );
}
