# ProductHunter Client

Vite + React + TypeScript frontend for ProductHunter.

## Features
- Landing screen that launches the app experience.
- Search/Compare tab backed by `/api/v1/products/search`.
- Product detail view with seller comparison, price history, deal analysis, wishlist, and price-alert controls.
- Trending Deals tab backed by `/api/v1/platform_products/platform-products/trending`.
- Wishlist and Price Alerts tabs for authenticated users.
- Email/password auth, forgot/reset password, and Google/GitHub OAuth redirects.
- ProductHunter Advisor widget backed by `/api/v1/advisor/chat`.
- Theme and language context providers.

## Configuration

The API base URL is currently defined in `src/config.ts`:

```ts
export const CONFIG = {
  API_URL: "https://nanopi-r5c.tail47f64f.ts.net/api/v1"
};
```

Change this value for local development if the backend is running at
`http://localhost:8000/api/v1`.

## Run Locally

```bash
npm install
npm run dev
```

The Vite dev server runs on port `3000`.

## Build and Test

```bash
npm run build
npm run test
npm run lint
```
