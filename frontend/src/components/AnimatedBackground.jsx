// Renderiza una nube de color animada para dar profundidad al diseño.
import { motion } from "framer-motion";

const blobs = [
  { size: 520, top: "-20%", left: "-20%", color: "rgba(123, 77, 255, 0.35)" },
  { size: 420, top: "40%", left: "70%", color: "rgba(61, 217, 181, 0.22)" },
  { size: 360, top: "70%", left: "10%", color: "rgba(255, 185, 101, 0.16)" },
];

export function AnimatedBackground() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
        zIndex: 0,
      }}
    >
      {blobs.map((blob, index) => (
        <motion.span
          key={index}
          initial={{ opacity: 0.4, scale: 0.8 }}
          animate={{ opacity: 0.75, scale: 1 }}
          transition={{
            duration: 3 + index,
            repeat: Infinity,
            repeatType: "reverse",
            ease: "easeInOut",
          }}
          style={{
            position: "absolute",
            width: blob.size,
            height: blob.size,
            background: blob.color,
            filter: "blur(120px)",
            borderRadius: "50%",
            top: blob.top,
            left: blob.left,
          }}
        />
      ))}
    </div>
  );
}
