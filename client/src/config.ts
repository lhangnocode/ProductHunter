const FALLBACK_PROD_API_URL = "https://nanopi-r5c.tail47f64f.ts.net/api/v1";
const DEV_API_URL = "http://localhost:8000/api/v1";

function resolveApiUrl(): string {
   const envUrl = import.meta.env.VITE_API_URL;
   if (envUrl) return envUrl;
   if (import.meta.env.DEV) return DEV_API_URL;
   return FALLBACK_PROD_API_URL;
}

export const CONFIG = {
   API_URL: resolveApiUrl(),
};
