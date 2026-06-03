# Frontend Service Tests - ProductHunter

## Overview

This document describes the comprehensive test suite for all frontend services in ProductHunter, following backend testing patterns established in the backend tests.

## Testing Structure

All frontend service tests are located in `client/src/services/__tests__/` and use **Vitest** as the testing framework with **happy-dom** as the environment.

### Test Files

1. **auth.test.ts** - Authentication service tests
2. **agent.test.ts** - Dashboard telesales agent service tests
3. **priceAlert.test.ts** - Price alert management tests
4. **wishlist.test.ts** - Wishlist management tests
5. **trending_deal_api.test.ts** - Trending deals API tests
6. **price_record_api.test.ts** - Product search and price record tests

## Testing Patterns

### 1. **Mocking Strategy**

All tests mock the global `fetch` API to avoid external dependencies:

```typescript
global.fetch = vi.fn();

beforeEach(() => {
  vi.resetAllMocks();
});
```

### 2. **Test Organization**

Tests are organized by service method using `describe` blocks:

```typescript
describe('authService', () => {
  describe('login', () => {
    it('should login successfully...', async () => {});
    it('should throw error with invalid credentials...', async () => {});
  });
  
  describe('register', () => {
    it('should register user successfully...', async () => {});
  });
});
```

### 3. **Error Handling**

Each service method is tested for:
- ✅ **Success Cases**: Valid input, successful API response
- ❌ **Error Cases**: Invalid input, API errors (400, 401, 403, 404, 422, 500)
- 🔄 **Edge Cases**: Null values, empty arrays, missing fields

### 4. **Assertions**

Tests verify:
1. **Correct API Endpoints**: URL construction with proper encoding
2. **Request Format**: Headers, method (GET/POST/DELETE), body
3. **Response Parsing**: Data normalization and transformation
4. **Error Messages**: Proper error handling and user-friendly messages

## Service Coverage

### auth.test.ts

**Covered Methods:**
- `login()` - User authentication with credentials
- `register()` - New user registration
- `forgotPassword()` - Password reset request
- `resetPassword()` - Password reset with token
- `getMe()` - Current user profile retrieval

**Key Test Cases:**
- ✅ Successful login with valid credentials
- ❌ Failed login with invalid credentials
- ✅ User registration with complete info
- ❌ Registration with duplicate email
- ✅ Token inclusion in Authorization header

### agent.test.ts

**Covered Methods:**
- `sendAgentMessage()` - Send a dashboard agent message over HTTP
- `streamAgentMessage()` - Stream dashboard agent events over HTTP SSE

**Key Test Cases:**
- ✅ Send message and receive recommendations
- ✅ Include chat history in requests
- ✅ Include context parameters
- ✅ Parse streamed agent events
- ❌ Handle API errors with detail messages

### priceAlert.test.ts

**Covered Methods:**
- `getAlerts()` - Fetch user's price alerts
- `setAlert()` - Create or update price alert
- `removeAlert()` - Delete price alert
- `triggerPriceCheck()` - Manually trigger price checking

**Key Test Cases:**
- ✅ Fetch alerts list with product details
- ✅ Create new price alert
- ✅ Update existing alert
- ✅ Delete alert by product ID
- ✅ Handle empty alerts list
- ✅ Trigger price check and parse results

### wishlist.test.ts

**Covered Methods:**
- `getWishlist()` - Fetch wishlist items
- `addToWishlist()` - Add product to wishlist
- `removeFromWishlist()` - Remove product from wishlist

**Key Test Cases:**
- ✅ Fetch wishlist with product details
- ✅ Add new product to wishlist
- ✅ Remove product from wishlist
- ❌ Handle duplicate products
- ✅ Return empty array on network errors
- ✅ Log errors appropriately

### trending_deal_api.test.ts

**Covered Methods:**
- `fetchTrendingDeals()` - Get trending products/deals

**Key Test Cases:**
- ✅ Fetch trending deals with limit parameter
- ✅ Handle 20 item default limit
- ✅ Parse deals with varying data (null prices)
- ✅ Include platform information
- ❌ Handle API errors (404, 500)
- ✅ Return empty array on error

### price_record_api.test.ts

**Covered Methods:**
- `searchProducts()` - Search products with pagination
- `searchPlatformProducts()` - Find products on specific platforms

**Key Test Cases:**
- ✅ Search with query string
- ✅ Support pagination (page, size)
- ✅ Normalize numeric fields
- ✅ Handle multiple response envelope formats
- ✅ Handle null prices
- ✅ Encode special characters in URLs
- ❌ Handle various error statuses

## Running Tests

### Run All Tests
```bash
npm run test
```

### Run Tests in Watch Mode
```bash
npm run test -- --watch
```

### Run Tests with Coverage Report
```bash
npm run test -- --coverage
```

### Run Specific Test File
```bash
npm run test -- auth.test.ts
```

### Run Tests Matching Pattern
```bash
npm run test -- --grep "login"
```

## CI/CD Integration

### GitHub Actions Workflow

The CI pipeline (`.github/workflows/ci.yml`) includes:

1. **Client-CI Job**:
   - Checkout code
   - Setup Node.js 22
   - Install dependencies
   - Type-check (`npm run lint`)
   - **Run unit tests** (`npm run test -- --run`)
   - Generate coverage report
   - Build application

2. **Server-CI Job**:
   - Separate Python pytest suite
   - Runs independently

### Coverage Requirements

Current coverage thresholds (set in `vitest.config.ts`):
- **Lines**: 70%
- **Functions**: 70%
- **Branches**: 70%
- **Statements**: 70%

## Test Data and Mocking

### Mock Data Patterns

All tests use realistic mock data that matches backend API responses:

```typescript
const mockResponse = {
  access_token: 'test-token-123',
  refresh_token: 'refresh-token-456',
  token_type: 'bearer'
};
```

### Fetch Mocking

```typescript
(global.fetch as any).mockResolvedValueOnce({
  ok: true,
  json: async () => mockResponse
});
```

## Best Practices

### ✅ DO's

1. **Test both success and error cases**
2. **Verify API endpoints and HTTP methods**
3. **Check request headers and body format**
4. **Mock all external dependencies**
5. **Use descriptive test names**
6. **Group related tests with describe blocks**
7. **Clean up mocks in beforeEach**
8. **Test error messages**

### ❌ DON'Ts

1. **Don't make actual API calls**
2. **Don't test third-party libraries**
3. **Don't create shared state between tests**
4. **Don't ignore error cases**
5. **Don't use ambiguous test names**

## Extending Tests

### Adding Tests for New Services

1. Create `new-service.test.ts` in `__tests__/` folder
2. Follow the established pattern:
   ```typescript
   import { describe, it, expect, vi, beforeEach } from 'vitest';
   import { newService } from '../new-service';

   global.fetch = vi.fn();

   describe('newService', () => {
     beforeEach(() => {
       vi.resetAllMocks();
     });
     
     describe('methodName', () => {
       it('should...', async () => {});
     });
   });
   ```

### Updating Existing Tests

1. Locate the service test file
2. Add new test cases under the appropriate `describe` block
3. Run tests to ensure they pass
4. Update this documentation if needed

## Debugging Tests

### Enable Verbose Output
```bash
npm run test -- --reporter=verbose
```

### Debug Single Test
```bash
npm run test -- --reporter=verbose auth.test.ts --grep "login"
```

### Use Console Output
```typescript
console.log('Debug output:', variable);
```

## Performance Considerations

- Tests run in happy-dom environment (lighter than JSDOM)
- Mocked fetch prevents network latency
- Parallel test execution by default
- Average test suite completion: ~2-3 seconds

## Common Issues and Solutions

### Issue: Tests fail with "fetch is not a function"
**Solution**: Ensure `global.fetch = vi.fn()` is defined before tests

### Issue: Mock not being called
**Solution**: Check that `vi.resetAllMocks()` in beforeEach isn't clearing necessary mocks

### Issue: Token not included in request
**Solution**: Verify authorization header is properly constructed in service

## References

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Backend Test Suite](../../server/tests/)
- [Service Implementation](../services/)

## Maintenance

- **Review Tests**: When service APIs change
- **Update Mocks**: When backend API responses change
- **Monitor Coverage**: Keep coverage above 70%
- **Refactor**: Apply new patterns to existing tests

---

**Last Updated**: 2024-01-29  
**Maintainer**: Frontend Team  
**Related Docs**: [Backend Tests](../../server/tests/README.md), [API Documentation](../../API_Docs.md)
