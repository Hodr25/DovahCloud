// Cliente ligero para comunicarnos con la API Flask usando fetch.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:5000/api";

// Ejecuta una petición con las opciones necesarias para mantener la sesión.
async function apiFetch(path, options = {}) {
  const finalOptions = { ...options };
  const isFormData = finalOptions.body instanceof FormData;
  const headers = new Headers(finalOptions.headers || {});

  if (isFormData) {
    headers.delete("Content-Type");
  } else {
    headers.set("Content-Type", "application/json");
  }

  finalOptions.credentials = "include";
  finalOptions.headers = headers;

  const response = await fetch(`${API_BASE_URL}${path}`, finalOptions);

  let payload = null;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    payload = await response.json();
  } else {
    payload = await response.text();
  }

  if (!response.ok) {
    const error = new Error("Solicitud rechazada por el servidor.");
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

// Acceso simplificado para GET.
export function apiGet(path) {
  return apiFetch(path, { method: "GET" });
}

// Acceso simplificado para POST con JSON.
export function apiPost(path, body, options = {}) {
  const finalOptions = { method: "POST", ...options };
  if (body instanceof FormData) {
    finalOptions.body = body;
  } else {
    finalOptions.body = JSON.stringify(body ?? {});
  }
  return apiFetch(path, finalOptions);
}

// Acceso simplificado para DELETE.
export function apiDelete(path) {
  return apiFetch(path, { method: "DELETE" });
}

export { API_BASE_URL };
