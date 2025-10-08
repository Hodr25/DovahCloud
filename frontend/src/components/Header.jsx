// Barra superior con búsqueda contextual y acciones rápidas.
import { motion } from "framer-motion";

export function Header({
  user,
  search,
  onSearchChange,
  onOpenUpload,
  onToggleFavorites,
  showFavorites,
  onRefresh,
  onLogout,
}) {
  // Renderiza el avatar con iniciales cuando no hay imagen.
  const initials = user?.username?.slice(0, 2)?.toUpperCase() ?? "";

  return (
    <motion.header
      className="glass-panel"
      style={{
        marginBottom: "1.8rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "1.4rem 1.8rem",
        position: "relative",
        overflow: "hidden",
      }}
      initial={{ opacity: 0, y: -18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "1.2rem" }}>
        <div>
          <h2 style={{ fontSize: "1.65rem", fontWeight: 600 }}>Panel multimedia</h2>
          <p style={{ color: "var(--color-text-secondary)", fontSize: "0.95rem" }}>
            Bienvenido de nuevo, {user?.username}. Gestiona tus archivos con fluidez.
          </p>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1.2rem" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.6rem",
            background: "rgba(10, 4, 22, 0.7)",
            borderRadius: "var(--radius-sm)",
            border: "1px solid rgba(123, 77, 255, 0.25)",
            padding: "0.35rem 0.6rem 0.35rem 0.9rem",
          }}
        >
          <span style={{ opacity: 0.6 }}>🔍</span>
          <input
            type="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Buscar por nombre, tipo o descripción..."
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: "var(--color-text-primary)",
              width: "280px",
            }}
          />
        </div>

        <button
          className="ghost-button"
          style={{
            paddingInline: "1.1rem",
            display: "flex",
            alignItems: "center",
            gap: "0.45rem",
            background: showFavorites ? "rgba(123, 77, 255, 0.18)" : "transparent",
            borderColor: showFavorites ? "rgba(123, 77, 255, 0.6)" : undefined,
            color: showFavorites ? "var(--color-text-primary)" : undefined,
          }}
          onClick={onToggleFavorites}
        >
          {showFavorites ? "★" : "☆"} Favoritos
        </button>

        <button className="ghost-button" onClick={onRefresh}>
          ↻ Actualizar
        </button>

        <button className="ghost-button" onClick={onLogout}>
          Salir
        </button>

        <button className="primary-button" onClick={onOpenUpload}>
          Subir archivo
        </button>

        <div
          style={{
            width: "48px",
            height: "48px",
            borderRadius: "16px",
            background: "linear-gradient(135deg, rgba(123, 77, 255, 0.65), rgba(123, 77, 255, 0.35))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
            letterSpacing: "0.04em",
            color: "#fff",
          }}
        >
          {initials}
        </div>
      </div>
    </motion.header>
  );
}
