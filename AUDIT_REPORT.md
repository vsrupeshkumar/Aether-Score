# AETHER-SCORE Codebase Audit Report
**Date:** 2025-12-15  
**Auditor:** Senior Blockchain + Full-Stack Engineer  
**Scope:** Functional bugs, silent failures, testnet resilience, UX issues, security risks

---

## Executive Summary

This audit identified **47 issues** across 5 categories:
- **Infrastructure:** 8 issues
- **Smart Contracts:** 5 issues  
- **Backend:** 18 issues
- **Frontend:** 10 issues
- **UX/DX:** 6 issues

**Priority Breakdown:**
- ðŸ”´ **Critical (P0):** 12 issues - Can break core functionality or cause data loss
- ðŸŸ  **High (P1):** 18 issues - Significantly impacts user experience or reliability
- ðŸŸ¡ **Medium (P2):** 12 issues - Minor bugs or edge cases
- ðŸŸ¢ **Low (P3):** 5 issues - Code quality or minor improvements

---

## ðŸ”´ CRITICAL ISSUES (P0)

### Infrastructure

**1. No RPC Failover/Retry Logic**
- **Location:** `backend/services/blockchain.py:15`, `backend/utils/rpc_pool.py:23`
- **Issue:** Single RPC endpoint with no fallback. If `rpc1testnet.qie.digital` goes down, entire app fails.
- **Impact:** Complete service outage during testnet instability
- **Fix:** Implement multi-RPC fallback with health checks

**2. Transaction Receipt Wait Has No Timeout**
- **Location:** `backend/services/blockchain.py:175`
- **Issue:** `wait_for_transaction_receipt()` can hang indefinitely if transaction never confirms
- **Impact:** API requests hang forever, blocking workers
- **Fix:** Add timeout parameter (e.g., 5 minutes) with proper error handling

**3. Global Exception Handler Returns Wrong Type**
- **Location:** `backend/app.py:91-108`
- **Issue:** Returns `HTTPException` object instead of `Response`, causing 500 error on all exceptions
- **Impact:** All errors return malformed responses
- **Fix:** Return proper `JSONResponse` with status code

**4. CORS Allows All Origins with Credentials**
- **Location:** `backend/app.py:116`
- **Issue:** `allow_origins=["*"]` with `allow_credentials=True` is invalid and insecure
- **Impact:** Browser rejects requests, CORS errors in production
- **Fix:** Either remove credentials or specify exact origins

### Smart Contracts

**5. Missing Reentrancy Protection in LendingVault**
- **Location:** `contracts/contracts/LendingVaultV2.sol:213-219`
- **Issue:** External call (`transfer`) before state updates in `createLoan()`
- **Impact:** Potential reentrancy attacks
- **Fix:** Use Checks-Effects-Interactions pattern or ReentrancyGuard

**6. No Gas Limit Validation**
- **Location:** `backend/services/blockchain.py:163`
- **Issue:** Hardcoded `gas: 200000` may be insufficient for complex transactions
- **Impact:** Transactions fail with out-of-gas errors
- **Fix:** Estimate gas dynamically or use higher limit with validation

### Backend

**7. Silent Failure in Score Computation**
- **Location:** `backend/services/scoring.py:119-148`
- **Issue:** Returns default score (500) on ANY error, masking real failures
- **Impact:** Users get incorrect scores, no error visibility
- **Fix:** Log error, return proper error response, only use default for specific cases

**8. Nonce Collision Risk**
- **Location:** `backend/core/nonce.py:38-66`
- **Issue:** In-memory nonce generation uses `time.time()` as base, can collide across restarts
- **Impact:** Replay attacks possible after server restart
- **Fix:** Use persistent storage (Redis) or database-backed nonce

**9. Private Key Not Sanitized in BlockchainService**
- **Location:** `backend/services/blockchain.py:26`
- **Issue:** Private key passed directly to `Account.from_key()` without sanitization
- **Impact:** Same "Non-hexadecimal digit" errors as LoanOfferSigner
- **Fix:** Apply same sanitization logic as `core/signing.py`

**10. Missing Address Validation in Chat Endpoint**
- **Location:** `backend/app.py:580`
- **Issue:** `chat_request.address` passed directly to agent without validation
- **Impact:** Invalid addresses cause cryptic errors
- **Fix:** Validate address format before processing

**11. Oracle Service Returns None Silently**
- **Location:** `backend/services/oracle.py:56-57`
- **Issue:** Errors return `None` without logging context
- **Impact:** Scoring uses wrong values, no visibility into failures
- **Fix:** Log errors with context, return structured error response

**12. No Rate Limiting on Critical Endpoints**
- **Location:** `backend/app.py:552`
- **Issue:** Chat endpoint has rate limit but score generation doesn't
- **Impact:** DDoS vulnerability, excessive RPC calls
- **Fix:** Add rate limiting to `/api/score` and `/api/update-on-chain`

---

## ðŸŸ  HIGH PRIORITY ISSUES (P1)

### Infrastructure

**13. RPC Pool Uses Single URL**
- **Location:** `backend/utils/rpc_pool.py:23`
- **Issue:** All connections point to same RPC, no load distribution
- **Impact:** Single point of failure, no redundancy
- **Fix:** Support multiple RPC URLs with round-robin/health checks

**14. No Connection Health Monitoring**
- **Location:** `backend/utils/rpc_pool.py:39-47`
- **Issue:** Pool doesn't check if connections are alive before use
- **Impact:** Dead connections cause timeouts
- **Fix:** Add health checks, remove dead connections from pool

**15. Hardcoded Timeout Values**
- **Location:** Multiple files (10s, 5s, 2s timeouts scattered)
- **Issue:** No configuration, may be too short for slow testnet
- **Impact:** Premature timeouts during network congestion
- **Fix:** Make timeouts configurable via env vars

### Smart Contracts

**16. Circuit Breaker Can Be Bypassed**
- **Location:** `contracts/contracts/CreditPassportNFTV2.sol:123`
- **Issue:** Circuit breaker check is inside `if (circuitBreakerConfig.enabled)`, can be disabled
- **Impact:** Admin can disable safety mechanisms
- **Fix:** Add minimum thresholds that can't be disabled

**17. No Maximum Loan Amount Check**
- **Location:** `contracts/contracts/LendingVaultV2.sol:180`
- **Issue:** Only checks `amount > 0`, no upper bound
- **Impact:** Potential integer overflow or excessive exposure
- **Fix:** Add maximum loan amount limit

### Backend

**18. Error Messages Expose Internal Details**
- **Location:** `backend/app.py:604`
- **Issue:** Development mode returns full error messages to users
- **Impact:** Information leakage, security risk
- **Fix:** Always sanitize error messages in production

**19. Missing Transaction Status Validation**
- **Location:** `backend/services/blockchain.py:175`
- **Issue:** Doesn't check `receipt.status` after waiting
- **Impact:** Failed transactions treated as successful
- **Fix:** Validate `receipt.status == 1` before returning

**20. Score History Save Can Fail Silently**
- **Location:** `backend/services/scoring.py:111-112`
- **Issue:** Exception caught but only logged, no retry or alert
- **Impact:** Missing historical data, no audit trail
- **Fix:** Add retry logic, alert on persistent failures

**21. Gas Price Not Validated**
- **Location:** `backend/services/blockchain.py:164`
- **Issue:** Uses `w3.eth.gas_price` directly, could be 0 or extremely high
- **Impact:** Transactions fail or waste funds
- **Fix:** Validate gas price is within reasonable bounds

**22. No Retry Logic for RPC Calls**
- **Location:** `backend/services/blockchain.py:116`, `backend/utils/rpc_pool.py:147`
- **Issue:** Single attempt, fails immediately on network hiccup
- **Impact:** Transient network issues cause permanent failures
- **Fix:** Implement exponential backoff retry (3 attempts)

**23. Chat Agent Swallows Exceptions**
- **Location:** `backend/core/agent.py:124-126`
- **Issue:** Returns default score on ANY exception, no logging
- **Impact:** Errors invisible, debugging impossible
- **Fix:** Log exception details, only use default for specific cases

**24. Missing Input Sanitization in Chat**
- **Location:** `backend/app.py:565`
- **Issue:** Message sanitized but address not validated
- **Impact:** Invalid addresses cause downstream errors
- **Fix:** Validate address format before processing

**25. Loan Offer Signature Can Be Placeholder**
- **Location:** `backend/core/agent.py:186-196`
- **Issue:** Uses `0x0...0` signature if signing fails, no error to user
- **Impact:** Invalid offers accepted, transactions fail on-chain
- **Fix:** Fail fast if signature generation fails

**26. No Validation of Score Range**
- **Location:** `backend/services/scoring.py:40`
- **Issue:** `max(0, min(1000, ...))` clamps but doesn't warn on edge cases
- **Impact:** Scores at boundaries may indicate calculation errors
- **Fix:** Log warnings when scores hit boundaries

**27. Database Connection Pool Not Configured**
- **Location:** `backend/database/connection.py:42`
- **Issue:** Pool size/timeout may be insufficient for load
- **Impact:** Connection exhaustion under load
- **Fix:** Tune pool settings based on expected load

**28. Missing Circuit Breaker in Backend**
- **Location:** `backend/services/blockchain.py`
- **Issue:** No rate limiting or circuit breaker for RPC calls
- **Impact:** RPC overload can crash service
- **Fix:** Add circuit breaker pattern for RPC calls

### Frontend

**29. No Error Boundary for Chat Component**
- **Location:** `frontend/app/components/ChatConsole.tsx`
- **Issue:** Unhandled errors crash entire chat UI
- **Impact:** Poor UX, no recovery path
- **Fix:** Add error boundary, show user-friendly error message

**30. Network Error Messages Expose Internal URLs**
- **Location:** `frontend/app/components/ChatConsole.tsx:80`
- **Issue:** Error message includes backend URL
- **Impact:** Information leakage, confusing for users
- **Fix:** Show generic "Connection error" message

**31. Missing Loading States**
- **Location:** `frontend/app/lend/page.tsx:199`
- **Issue:** No loading indicator during loan creation
- **Impact:** Users don't know transaction is processing
- **Fix:** Add loading spinner/disabled state

**32. No Transaction Confirmation Feedback**
- **Location:** `frontend/app/lend/page.tsx:201`
- **Issue:** Only shows alert, no visual confirmation
- **Impact:** Users may miss success/failure
- **Fix:** Add toast notification with transaction hash

**33. Wallet Connection Errors Not User-Friendly**
- **Location:** `frontend/app/contexts/WalletContext.tsx:310-315`
- **Issue:** Generic "Failed to connect" message
- **Impact:** Users don't know how to fix issue
- **Fix:** Provide specific error messages (e.g., "Please unlock MetaMask")

**34. No Retry for Failed API Calls**
- **Location:** `frontend/lib/api.ts`, `frontend/app/components/ChatConsole.tsx:44`
- **Issue:** Single attempt, fails immediately
- **Impact:** Transient network issues break UX
- **Fix:** Add retry logic with exponential backoff

**35. Missing Input Validation**
- **Location:** `frontend/app/components/ChatConsole.tsx:33`
- **Issue:** Only checks `trim()`, no length/character validation
- **Impact:** Extremely long messages or special chars may break backend
- **Fix:** Validate message length and sanitize input

**36. Hardcoded Contract Address Check**
- **Location:** `frontend/app/lend/page.tsx:55`
- **Issue:** Checks for placeholder addresses but logic is fragile
- **Impact:** May skip valid contract addresses
- **Fix:** Use proper validation, check contract code existence

**37. No Fallback for RPC Failures**
- **Location:** `frontend/app/lend/page.tsx:116-141`
- **Issue:** Attempts fallback but logic is incomplete
- **Impact:** RPC failures still break loan creation
- **Fix:** Implement proper RPC fallback chain

**38. Signature Normalization Logic Is Fragile**
- **Location:** `frontend/app/lend/page.tsx:148-179`
- **Issue:** Complex normalization, may fail on edge cases
- **Impact:** Valid signatures rejected
- **Fix:** Use ethers.js built-in validation

---

## ðŸŸ¡ MEDIUM PRIORITY ISSUES (P2)

### Infrastructure

**39. No Metrics for RPC Latency**
- **Location:** `backend/utils/rpc_pool.py`
- **Issue:** No tracking of RPC call duration
- **Impact:** Can't identify slow RPC endpoints
- **Fix:** Add timing metrics to all RPC calls

**40. Cache TTL Not Configured**
- **Location:** `backend/utils/cache.py`
- **Issue:** Cache expiration times may be too long/short
- **Impact:** Stale data or excessive cache misses
- **Fix:** Make TTL configurable per cache type

### Smart Contracts

**41. Events Don't Include All Relevant Data**
- **Location:** `contracts/contracts/LendingVaultV2.sol:83-104`
- **Issue:** `LoanCreated` doesn't include expiry or nonce
- **Impact:** Harder to track offer lifecycle
- **Fix:** Add missing fields to events

**42. No Pause Delay**
- **Location:** `contracts/contracts/CreditPassportNFTV2.sol:219`
- **Issue:** Pause is immediate, no timelock
- **Impact:** Admin can pause instantly (centralization risk)
- **Fix:** Add timelock for pause (e.g., 24 hours)

### Backend

**43. Logging Levels Not Consistent**
- **Location:** Multiple files
- **Issue:** Mix of `print()`, `logger.info()`, `logger.error()`
- **Impact:** Inconsistent log levels, hard to filter
- **Fix:** Standardize on structured logging

**44. Missing Type Hints**
- **Location:** `backend/core/agent.py:200`
- **Issue:** `_extract_amount()` returns `Optional[float]` but implementation unclear
- **Impact:** Type errors, harder to maintain
- **Fix:** Add proper type hints throughout

**45. Hardcoded Magic Numbers**
- **Location:** `backend/core/agent.py:145-159`
- **Issue:** Interest rates, LTV ratios hardcoded
- **Impact:** Can't adjust without code changes
- **Fix:** Move to configuration file or database

**46. No Validation of Risk Band Range**
- **Location:** `backend/services/scoring.py:43-45`
- **Issue:** Risk band can be adjusted but not validated
- **Impact:** Invalid risk bands (e.g., 0 or 4) possible
- **Fix:** Validate risk band is 1-3

**47. Missing Async Context Managers**
- **Location:** `backend/services/scoring.py:322`
- **Issue:** Database session not using async context manager properly
- **Impact:** Potential connection leaks
- **Fix:** Use proper async context managers

### Frontend

**48. No Debouncing on Chat Input**
- **Location:** `frontend/app/components/ChatConsole.tsx:32`
- **Issue:** Can send multiple messages rapidly
- **Impact:** Spam, unnecessary API calls
- **Fix:** Add debouncing or disable send while loading

**49. Missing Accessibility Attributes**
- **Location:** `frontend/app/components/ChatConsole.tsx:212`
- **Issue:** Input and buttons lack ARIA labels
- **Impact:** Poor accessibility
- **Fix:** Add proper ARIA attributes

**50. No Offline Detection**
- **Location:** `frontend/app/components/ChatConsole.tsx`
- **Issue:** No check if user is offline
- **Impact:** Errors when offline, poor UX
- **Fix:** Check `navigator.onLine`, show offline message

---

## ðŸŸ¢ LOW PRIORITY ISSUES (P3)

### UX/DX

**51. Confusing Error Messages for Judges**
- **Location:** `frontend/app/components/ChatConsole.tsx:88`
- **Issue:** "Internal server error" not helpful for demo
- **Impact:** Judges see technical errors
- **Fix:** Show user-friendly messages (e.g., "Service temporarily unavailable")

**52. No Loading Skeleton**
- **Location:** `frontend/app/lend/page.tsx:267`
- **Issue:** Score display shows nothing while loading
- **Impact:** Blank screen, confusing UX
- **Fix:** Add loading skeleton component

**53. Missing Tooltips**
- **Location:** `frontend/app/lend/page.tsx:244`
- **Issue:** No explanation of what AETHER-SCORE score means
- **Impact:** Judges may not understand scoring
- **Fix:** Add tooltips with explanations

**54. No Demo Mode Indicator**
- **Location:** `frontend/app/layout.tsx`
- **Issue:** No clear indication this is a testnet/demo
- **Impact:** Judges may think it's production
- **Fix:** Add banner indicating testnet/demo mode

**55. Hardcoded Text Strings**
- **Location:** Multiple frontend files
- **Issue:** No i18n support, all text in English
- **Impact:** Limited accessibility
- **Fix:** Add i18n framework (already have `lib/i18n.ts` but not used)

**56. No Error Recovery Suggestions**
- **Location:** `frontend/app/components/ChatConsole.tsx:84-90`
- **Issue:** Errors don't suggest how to fix
- **Impact:** Users stuck, don't know what to do
- **Fix:** Add actionable error messages (e.g., "Please refresh the page")

---

## Testnet-Specific Risks

### High Risk

1. **RPC Endpoint Instability**
   - Single endpoint, no fallback
   - 10s timeout may be too short during congestion
   - No health monitoring

2. **Transaction Confirmation Delays**
   - No timeout on `wait_for_transaction_receipt()`
   - Can hang indefinitely if testnet is slow
   - No retry logic for failed transactions

3. **Gas Price Volatility**
   - Uses current gas price without validation
   - Testnet gas prices can spike
   - No maximum gas price cap

### Medium Risk

4. **Network Switching Issues**
   - Frontend prompts for network switch but may fail
   - No automatic retry
   - Confusing error messages

5. **Contract Deployment Status**
   - Frontend checks for contract code but logic is fragile
   - May skip valid contracts or accept invalid ones

---

## Security Concerns

### Critical

1. **CORS Misconfiguration** (P0)
   - `allow_origins=["*"]` with `allow_credentials=True` is invalid
   - Should specify exact origins or remove credentials

2. **Private Key Handling** (P0)
   - Private keys in environment variables (even if encrypted)
   - Should use hardware security modules or key management services

3. **No Input Validation** (P1)
   - Address validation missing in several places
   - Message length validation exists but may be insufficient

### Medium

4. **Error Message Leakage** (P1)
   - Development error messages exposed in production
   - Stack traces may leak sensitive information

5. **Rate Limiting Gaps** (P1)
   - Some endpoints not rate limited
   - Potential for DDoS or abuse

---

## Recommendations

### Immediate Actions (Before Demo)

1. Fix CORS configuration (Issue #4)
2. Add timeout to transaction receipt wait (Issue #2)
3. Fix global exception handler (Issue #3)
4. Add RPC fallback mechanism (Issue #1)
5. Improve error messages for judges (Issue #51)

### Short Term (Post-Demo)

1. Implement proper retry logic for RPC calls
2. Add circuit breakers for external services
3. Improve error handling and logging
4. Add comprehensive input validation
5. Implement proper rate limiting

### Long Term

1. Move to production-grade infrastructure
2. Implement proper key management
3. Add comprehensive monitoring and alerting
4. Security audit of smart contracts
5. Performance optimization and load testing

---

## Testing Gaps

1. **No Integration Tests for RPC Failures**
   - Should test behavior when RPC is down
   - Test timeout scenarios
   - Test retry logic

2. **No End-to-End Tests for Loan Flow**
   - Should test complete loan creation flow
   - Test error scenarios
   - Test network switching

3. **No Load Testing**
   - Unknown behavior under load
   - Connection pool may be insufficient
   - Database may bottleneck

---

## Conclusion

The codebase is **functional for a hackathon demo** but has several critical issues that could cause failures during judging. Priority should be given to:

1. **RPC resilience** - Most critical for testnet stability
2. **Error handling** - Critical for user experience
3. **CORS configuration** - Blocks frontend-backend communication
4. **Transaction timeouts** - Can hang indefinitely

Most issues are fixable with 1-2 days of focused work. The smart contract issues are more serious and would require audit, but for a hackathon demo, the current implementation should work with the backend fixes.

---

**Next Steps:**
1. Review this report with team
2. Prioritize fixes based on demo timeline
3. Create tickets for each issue
4. Implement fixes in priority order
5. Test fixes in testnet environment

