// Hook reutilizable para orquestar llamadas a la API con control de estado.
import { useCallback, useState } from "react";

export function useApi(asyncFunction, defaultConfig = {}) {
  // Representa si la llamada está en curso.
  const [loading, setLoading] = useState(false);
  // Almacena el último error recibido.
  const [error, setError] = useState(null);

  // Ejecuta la acción remota y devuelve el resultado.
  const execute = useCallback(
    async (...args) => {
      setLoading(true);
      setError(null);

      try {
        const result = await asyncFunction(...args);
        return result;
      } catch (err) {
        setError(err);
        if (defaultConfig.throwOnError) {
          throw err;
        }
        return null;
      } finally {
        setLoading(false);
      }
    },
    [asyncFunction, defaultConfig.throwOnError]
  );

  return { execute, loading, error };
}
