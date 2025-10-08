// Sistema simple de notificaciones apiladas para feedback rápido.
import { AnimatePresence, motion } from "framer-motion";

export function NotificationStack({ messages, onDismiss }) {
  return (
    <div
      style={{
        position: "fixed",
        right: "2rem",
        bottom: "2rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.8rem",
        zIndex: 60,
      }}
    >
      <AnimatePresence>
        {messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.25 }}
            className="glass-panel"
            style={{
              padding: "1rem 1.2rem",
              minWidth: "260px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "1rem",
            }}
          >
            <div>
              <strong style={{ display: "block" }}>{message.title}</strong>
              <p style={{ fontSize: "0.9rem", color: "var(--color-text-secondary)" }}>{message.body}</p>
            </div>
            <button className="ghost-button" onClick={() => onDismiss(message.id)}>
              Cerrar
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
