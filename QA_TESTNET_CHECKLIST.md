# QA Testnet Reliability Checklist

## 🎯 Purpose
Comprehensive test checklist to identify failure points, race conditions, and unsafe assumptions before mainnet deployment.

**Constraints:**
- NO mainnet deployment
- NO gas spending
- Assume hostile or careless users

---

## 🔴 CRITICAL: Wallet & Network Failures

### 1. Wallet Disconnection During Operations
**Test Cases:**
- [ ] **During transaction signing**: Disconnect wallet while MetaMask popup is open
  - Expected: Transaction should be cancelled, UI should show disconnected state
  - Risk: Transaction might be submitted with wrong account or fail silently
  
- [ ] **During transaction confirmation**: Disconnect wallet while `tx.wait()` is pending
  - Expected: Error should be caught, loading state cleared, user notified
  - Risk: UI stuck in loading state, transaction state lost
  
- [ ] **During balance refresh**: Disconnect wallet while fetching balance
  - Expected: Error handled gracefully, balance shows 0 or "Disconnected"
  - Risk: Stale balance displayed, incorrect UI state

**Manual Test Steps:**
1. Connect wallet
2. Start any transaction (staking, loan creation)
3. While MetaMask popup is open, disconnect wallet in MetaMask
4. Observe UI behavior and error messages

---

### 2. Network Switching During Operations
**Test Cases:**
- [ ] **Switch network during transaction signing**
  - Expected: Transaction should fail with clear error, page should reload
  - Risk: Transaction sent to wrong network, funds lost
  
- [ ] **Switch network during `tx.wait()`**
  - Expected: Transaction wait should timeout or fail, error shown
  - Risk: UI stuck waiting forever, transaction state unknown
  
- [ ] **Switch network while loading data** (score, loans, staking info)
  - Expected: Requests should be cancelled, error shown, or data cleared
  - Risk: Stale data from wrong network displayed

**Manual Test Steps:**
1. Connect wallet on QIE Testnet
2. Start a transaction (e.g., stake tokens)
3. While transaction is pending, switch to Ethereum Mainnet in MetaMask
4. Observe error handling and UI state

---

### 3. Account Switching
**Test Cases:**
- [ ] **Switch account during transaction**
  - Expected: Transaction should fail (wrong signer), error shown
  - Risk: Transaction sent from wrong account
  
- [ ] **Switch account while data is loading**
  - Expected: Data should refresh for new account, old data cleared
  - Risk: Data from old account shown for new account

**Manual Test Steps:**
1. Connect Account A
2. Start loading score/loans
3. Switch to Account B in MetaMask
4. Verify data updates correctly

---

## 🟠 HIGH: Transaction State & Race Conditions

### 4. Double-Submission Protection
**Test Cases:**
- [ ] **Rapid button clicks**: Click "Stake" or "Accept Offer" multiple times quickly
  - Expected: Only one transaction submitted, button disabled during processing
  - Risk: Multiple transactions, wasted gas, unexpected state
  
- [ ] **Transaction already pending**: Try to submit another transaction while one is pending
  - Expected: Second transaction blocked with clear message
  - Risk: Multiple pending transactions, state confusion

**Manual Test Steps:**
1. Click "Stake" button
2. Immediately click again 5-10 times before MetaMask popup appears
3. Verify only one transaction is created

---

### 5. Transaction Timeout Handling
**Test Cases:**
- [ ] **Slow RPC response**: Simulate slow RPC (use network throttling)
  - Expected: Transaction should timeout after reasonable time (30-60s), error shown
  - Risk: UI stuck forever, user doesn't know transaction status
  
- [ ] **Transaction stuck in mempool**: Transaction sent but never confirmed
  - Expected: Timeout after 5 minutes, show transaction hash, allow retry
  - Risk: User thinks transaction failed, but it's actually pending

**Manual Test Steps:**
1. Use browser DevTools to throttle network to "Slow 3G"
2. Submit a transaction
3. Verify timeout handling and error messages

---

### 6. Async Race Conditions
**Test Cases:**
- [ ] **Multiple simultaneous API calls**: Load score, loans, staking info at same time
  - Expected: All requests complete, no state corruption
  - Risk: Last response overwrites earlier ones, wrong data shown
  
- [ ] **Component unmount during async**: Navigate away while data is loading
  - Expected: Requests cancelled, no memory leaks, no errors in console
  - Risk: State updates on unmounted component, React warnings

**Manual Test Steps:**
1. Connect wallet
2. Rapidly navigate between Dashboard, Portfolio, Loans pages
3. Check console for errors and warnings

---

## 🟡 MEDIUM: Input Validation & Data Integrity

### 7. Invalid Input Handling
**Test Cases:**
- [ ] **Negative amounts**: Enter negative number for staking amount
  - Expected: Validation error, transaction blocked
  - Risk: Transaction might succeed with wrong amount
  
- [ ] **Zero amounts**: Enter 0 for staking/loan amounts
  - Expected: Validation error or clear message
  - Risk: Transaction succeeds but does nothing
  
- [ ] **Extremely large amounts**: Enter amount larger than balance
  - Expected: Error before transaction, "Insufficient balance" message
  - Risk: Transaction fails after user approval, wasted gas
  
- [ ] **Invalid characters**: Enter non-numeric characters in amount fields
  - Expected: Input rejected or sanitized
  - Risk: `parseEther` throws error, UI breaks

**Manual Test Steps:**
1. Try to stake: `-100`, `0`, `999999999999`, `abc`, `1.5.5`
2. Verify validation and error messages

---

### 8. Signature Validation
**Test Cases:**
- [ ] **Invalid signature format**: Backend returns malformed signature
  - Expected: Error caught, clear message to user
  - Risk: Transaction sent with invalid signature, fails on-chain
  
- [ ] **Expired offer**: Use old loan offer with expired timestamp
  - Expected: Transaction should fail on-chain, error shown
  - Risk: Old offer accepted, wrong terms
  
- [ ] **Signature for wrong network**: Use testnet signature on mainnet
  - Expected: Transaction fails, error shown
  - Risk: Signature validation passes but wrong chain

**Manual Test Steps:**
1. Generate loan offer
2. Wait 5+ minutes (if expiry is short)
3. Try to accept offer
4. Verify expiry handling

---

### 9. BigInt & Number Overflow
**Test Cases:**
- [ ] **Very large amounts**: Amounts that exceed JavaScript number precision
  - Expected: BigInt used correctly, no precision loss
  - Risk: Amounts rounded incorrectly, wrong transaction values
  
- [ ] **formatOffer division**: ChatConsole divides by 1e18 (line 108-111)
  - Expected: Handles BigInt correctly, no precision loss
  - Risk: Amounts displayed incorrectly in UI

**Manual Test Steps:**
1. Request loan for very large amount (e.g., 1e20 wei)
2. Verify amounts displayed correctly in chat offer
3. Verify transaction uses correct amount

---

## 🟢 LOW: Edge Cases & UX Issues

### 10. RPC Failover
**Test Cases:**
- [ ] **Primary RPC down**: Disable primary RPC endpoint
  - Expected: Automatic failover to backup RPC, no user-visible error
  - Risk: All requests fail, app unusable
  
- [ ] **All RPCs down**: Disable all RPC endpoints
  - Expected: Clear error message, retry button
  - Risk: Silent failures, confusing UX

**Manual Test Steps:**
1. Block primary RPC in browser DevTools
2. Try to load score or submit transaction
3. Verify failover works

---

### 11. Page Reload During Operations
**Test Cases:**
- [ ] **Reload during transaction**: Refresh page while transaction is pending
  - Expected: Transaction continues in background, user can check status
  - Risk: Transaction state lost, user doesn't know if it succeeded
  
- [ ] **Reload after network switch**: Page auto-reloads on chain change
  - Expected: Reload happens cleanly, no errors
  - Risk: Reload during transaction, state corruption

**Manual Test Steps:**
1. Submit transaction
2. Immediately refresh page
3. Check if transaction status is preserved

---

### 12. Error Message Clarity
**Test Cases:**
- [ ] **RPC errors**: Check all RPC error messages are user-friendly
  - Expected: "Network error, please try again" not "ECONNREFUSED"
  - Risk: Users confused by technical errors
  
- [ ] **Transaction failures**: Check revert reasons are displayed
  - Expected: "Insufficient balance" not "execution reverted"
  - Risk: Users don't know why transaction failed

**Manual Test Steps:**
1. Submit transaction with insufficient balance
2. Verify error message is clear and actionable

---

### 13. Loading States
**Test Cases:**
- [ ] **Loading indicators**: All async operations show loading state
  - Expected: Button disabled, spinner shown, text indicates action
  - Risk: Users click multiple times, unclear if action is processing
  
- [ ] **Loading state cleanup**: Loading state cleared on error
  - Expected: Button re-enabled, spinner hidden, error shown
  - Risk: UI stuck in loading state forever

**Manual Test Steps:**
1. Submit transaction
2. Cancel in MetaMask
3. Verify loading state is cleared

---

## 🔵 BACKEND: API & Data Integrity

### 14. Backend Error Handling
**Test Cases:**
- [ ] **Database connection lost**: Stop PostgreSQL
  - Expected: Graceful error, 500 with clear message
  - Risk: Unhandled exception, app crashes
  
- [ ] **RPC connection lost**: Backend can't connect to blockchain
  - Expected: Error logged, fallback RPC used, or clear error returned
  - Risk: Silent failures, wrong data returned

**Manual Test Steps:**
1. Stop backend database
2. Try to generate score
3. Verify error handling

---

### 15. Rate Limiting
**Test Cases:**
- [ ] **Rapid API calls**: Send 100 requests in 1 second
  - Expected: Rate limit enforced, 429 errors returned
  - Risk: Backend overloaded, DoS vulnerability

**Manual Test Steps:**
1. Use browser console to send rapid API requests
2. Verify rate limiting works

---

## 🛡️ SECURITY: Hostile User Behavior

### 16. Malicious Inputs
**Test Cases:**
- [ ] **SQL injection**: Try SQL in address field (shouldn't work, but verify)
  - Expected: Input sanitized, no SQL execution
  - Risk: Database compromise
  
- [ ] **XSS attacks**: Try script tags in chat messages
  - Expected: Input sanitized, scripts not executed
  - Risk: XSS vulnerability
  
- [ ] **Invalid addresses**: Try non-address strings
  - Expected: Validation error, request rejected
  - Risk: Backend errors, data corruption

**Manual Test Steps:**
1. Try to send chat message: `<script>alert('xss')</script>`
2. Try to use address: `'; DROP TABLE users; --`
3. Verify sanitization

---

### 17. Replay Attacks
**Test Cases:**
- [ ] **Reuse old signatures**: Try to use signature from old offer
  - Expected: Transaction fails (nonce/expiry check)
  - Risk: Old offers accepted, wrong terms

**Manual Test Steps:**
1. Generate loan offer (note signature)
2. Generate new offer
3. Try to use old signature with new offer
4. Verify rejection

---

## 📋 Test Execution Log

**Date:** _______________
**Tester:** _______________
**Environment:** Testnet / Mainnet (circle one)

| Test # | Status | Notes | Critical Issues Found |
|--------|--------|-------|---------------------|
| 1.1    | ⬜ Pass / ⬜ Fail | | |
| 1.2    | ⬜ Pass / ⬜ Fail | | |
| 1.3    | ⬜ Pass / ⬜ Fail | | |
| 2.1    | ⬜ Pass / ⬜ Fail | | |
| 2.2    | ⬜ Pass / ⬜ Fail | | |
| 2.3    | ⬜ Pass / ⬜ Fail | | |
| ...    | ...    | ...   | ... |

---

## 🚨 Critical Issues Found

**List any critical issues discovered during testing:**

1. 
2. 
3. 

---

## ✅ Sign-Off

**All critical tests passed:** ⬜ Yes / ⬜ No

**Ready for mainnet:** ⬜ Yes / ⬜ No

**Blockers:**
- 
- 

**Notes:**
- 

